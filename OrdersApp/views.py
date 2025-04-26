from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from django.shortcuts import get_object_or_404
from django.db import transaction

from ProductsApp.models import Products, Reviews
from .models import Cart, CartItem, Order, OrderItem
from .serializers import (
    CartSerializer, CartItemSerializer, 
    OrderSerializer, OrderCreateSerializer, OrderStatusUpdateSerializer,
    ProductReviewSerializer
)

# --------------------------
# Cart Management API Views
# --------------------------

class CartView(APIView):
    """View for retrieving and managing the user's shopping cart"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get the current user's cart with all items"""
        cart = request.user.cart
        serializer = CartSerializer(cart)
        return Response(serializer.data)
    
    def delete(self, request):
        """Clear all items from the cart"""
        cart = request.user.cart
        cart.clear()
        return Response({"message": "Cart cleared successfully"}, status=status.HTTP_200_OK)


class CartItemView(APIView):
    """View for managing individual cart items"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Add item to cart or update quantity if it exists"""
        serializer = CartItemSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            # Return the updated cart
            cart_serializer = CartSerializer(request.user.cart)
            return Response(cart_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request, product_id):
        """Update the quantity of an item in the cart"""
        cart = request.user.cart
        
        try:
            cart_item = CartItem.objects.get(cart=cart, product__id=product_id)
            new_quantity = request.data.get('quantity', 0)
            
            if new_quantity <= 0:
                return Response(
                    {"error": "Quantity must be greater than zero"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if new_quantity > cart_item.product.stock:
                return Response(
                    {"error": "Quantity exceeds available stock"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            cart_item.quantity = new_quantity
            cart_item.save()
            
            # Return the updated cart
            cart_serializer = CartSerializer(cart)
            return Response(cart_serializer.data, status=status.HTTP_200_OK)
        except CartItem.DoesNotExist:
            return Response(
                {"error": "Product not found in cart"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def delete(self, request, product_id):
        """Remove an item from the cart"""
        cart = request.user.cart
        
        try:
            cart_item = CartItem.objects.get(cart=cart, product__id=product_id)
            cart_item.delete()
            
            # Return the updated cart
            cart_serializer = CartSerializer(cart)
            return Response(cart_serializer.data, status=status.HTTP_200_OK)
        except CartItem.DoesNotExist:
            return Response(
                {"error": "Product not found in cart"}, 
                status=status.HTTP_404_NOT_FOUND
            )


# --------------------------
# Order Management API Views
# --------------------------

class OrderListView(ListAPIView):
    """View for listing user orders"""
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return orders for current user or all orders for admin"""
        user = self.request.user
        if user.is_staff:
            return Order.objects.all().order_by('-created_at')
        return Order.objects.filter(user=user).order_by('-created_at')


class OrderDetailView(RetrieveAPIView):
    """View for retrieving order details"""
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Ensure users can only see their own orders unless admin"""
        user = self.request.user
        if user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=user)


class CreateOrderView(APIView):
    """View for creating a new order from cart items"""
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        """Create order from cart items"""
        serializer = OrderCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            order = serializer.save()
            order_serializer = OrderSerializer(order)
            return Response(order_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpdateOrderStatusView(APIView):
    """View for updating order status (admin only)"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def put(self, request, pk):
        """Update order status"""
        order = get_object_or_404(Order, pk=pk)
        serializer = OrderStatusUpdateSerializer(order, data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                OrderSerializer(order).data,
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CancelOrderView(APIView):
    """View for cancelling an order"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        """Cancel order if it's in a cancellable state"""
        user = request.user
        query = Order.objects.filter(pk=pk)
        
        # Only let admins cancel any order
        if not user.is_staff:
            query = query.filter(user=user)
            
        order = get_object_or_404(query)
        
        if not order.can_cancel():
            return Response(
                {"error": "This order cannot be cancelled in its current state"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = 'Cancelled'
        order.save()
        
        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_200_OK
        )


class OrderStatusView(APIView):
    """View for retrieving and updating order status"""
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        """Retrieve the status of a specific order"""
        try:
            order = Order.objects.get(id=order_id, user=request.user)
            return Response({"status": order.status}, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, order_id):
        """Update the status of a specific order"""
        try:
            order = Order.objects.get(id=order_id, user=request.user)
            new_status = request.data.get("status")
            if new_status not in dict(Order.STATUS_CHOICES):
                return Response({"error": "Invalid status."}, status=status.HTTP_400_BAD_REQUEST)

            order.status = new_status
            order.save()
            return Response({"message": "Order status updated successfully."}, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)


# --------------------------
# Review API Views
# --------------------------

class CreateProductReviewView(APIView):
    """View for creating product reviews from delivered orders"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Create a product review for a delivered order item"""
        serializer = ProductReviewSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            review = serializer.save()
            return Response(
                {"message": "Review created successfully"},
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
