from rest_framework import serializers
from .models import Order, OrderItem, Cart, CartItem
from ProductsApp.models import Products, Reviews


class ProductMiniSerializer(serializers.ModelSerializer):
    """Minimal Product representation for cart/order items"""
    class Meta:
        model = Products
        fields = ['id', 'name', 'image', 'price', 'stock']


class CartItemSerializer(serializers.ModelSerializer):
    """Serializer for cart items with product information"""
    product = ProductMiniSerializer(read_only=True)
    product_id = serializers.UUIDField(write_only=True, required=True)
    total_price = serializers.SerializerMethodField()
    
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'quantity', 'date_added', 'total_price']
        read_only_fields = ['id', 'date_added', 'product', 'total_price']
    
    def get_total_price(self, obj):
        return obj.get_total()
    
    def validate(self, data):
        """Validate product exists and has sufficient stock"""
        try:
            product = Products.objects.get(id=data['product_id'])
            if data['quantity'] > product.stock:
                raise serializers.ValidationError(
                    f"Cannot add {data['quantity']} items. Only {product.stock} in stock."
                )
        except Products.DoesNotExist:
            raise serializers.ValidationError("Product not found")
        
        return data
    
    def create(self, validated_data):
        product_id = validated_data.pop('product_id')
        product = Products.objects.get(id=product_id)
        
        # Get or create cart item
        cart = self.context['request'].user.cart
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': validated_data['quantity']}
        )
        
        # Update quantity if item already exists
        if not created:
            cart_item.quantity = validated_data['quantity']
            cart_item.save()
            
        return cart_item


class CartSerializer(serializers.ModelSerializer):
    """Serializer for cart with item details"""
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()
    total_items = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = ['id', 'created_at', 'updated_at', 'is_active', 'items', 'total_price', 'total_items']
    
    def get_total_price(self, obj):
        return obj.get_total_price()
    
    def get_total_items(self, obj):
        return obj.get_total_items()


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for product reviews"""
    class Meta:
        model = Reviews
        fields = ['id', 'product', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'created_at']


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for order items with product information if available"""
    product = ProductMiniSerializer(read_only=True)
    can_review = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'quantity', 'price', 'reviewed', 'can_review', 'total_price']
    
    def get_can_review(self, obj):
        return obj.can_review()
    
    def get_total_price(self, obj):
        return obj.get_total()


class OrderSerializer(serializers.ModelSerializer):
    """Complete Order serializer with item details"""
    items = OrderItemSerializer(many=True, read_only=True)
    user_name = serializers.SerializerMethodField()
    can_cancel = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'user', 'user_name', 'total_amount', 'payment_status', 'payment_method',
            'status', 'created_at', 'updated_at', 'delivered_at',
            'shipping_address', 'city', 'country', 'zip_code', 'phone_no',
            'items', 'can_cancel'
        ]
    
    def get_user_name(self, obj):
        return obj.user.username if obj.user else "Unknown"
    
    def get_can_cancel(self, obj):
        return obj.can_cancel()


class OrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new order from cart"""
    class Meta:
        model = Order
        fields = [
            'payment_method', 'shipping_address', 'city', 
            'country', 'zip_code', 'phone_no'
        ]
    
    def create(self, validated_data):
        user = self.context['request'].user
        cart = Cart.objects.get(user=user)
        
        # Check if cart has items
        if not cart.items.exists():
            raise serializers.ValidationError({"cart": "Cart is empty"})
        
        # Create the order
        order = Order.objects.create(
            user=user,
            from_cart=cart,
            total_amount=cart.get_total_price(),
            **validated_data
        )
        
        # Create order items from cart items
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                product_name=cart_item.product.name,
                quantity=cart_item.quantity,
                price=cart_item.product.price,
                original_cart_item=cart_item
            )
        
        # Clear the cart after creating order
        cart.clear()
        
        return order


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating order status"""
    class Meta:
        model = Order
        fields = ['status']
        
        
class ProductReviewSerializer(serializers.ModelSerializer):
    """Serializer for creating reviews from delivered orders"""
    order_item_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Reviews
        fields = ['rating', 'comment', 'order_item_id']
    
    def validate_order_item_id(self, value):
        try:
            order_item = OrderItem.objects.get(id=value)
            user = self.context['request'].user
            
            # Check if order belongs to user
            if order_item.order.user != user:
                raise serializers.ValidationError("You cannot review items from another user's order")
            
            # Check if order is delivered
            if not order_item.can_review():
                raise serializers.ValidationError("You can only review items from delivered orders")
            
            # Store for later use in create
            self.context['order_item'] = order_item
            
        except OrderItem.DoesNotExist:
            raise serializers.ValidationError("Order item not found")
        
        return value
    
    def create(self, validated_data):
        order_item = self.context['order_item']
        user = self.context['request'].user
        
        # Create the review
        review = Reviews.objects.create(
            user=user,
            product=order_item.product,
            rating=validated_data['rating'],
            comment=validated_data['comment']
        )
        
        # Mark order item as reviewed
        order_item.reviewed = True
        order_item.save()
        
        return review
