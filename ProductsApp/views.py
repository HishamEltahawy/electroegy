from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Avg
from rest_framework.views import APIView
from utils.recommendations import get_recommended_products
from .models import Products, Reviews
from OrdersApp.models import Order, OrderItem, Cart, CartItem
from .serializers import SzProducts, SzReview, ProductSerializer
from .filters import ProductFilters


def main(request):
    return render(request, 'main.html')

# To get all products on database
@api_view(['GET'])
def get_all_products(response): # api/products/all-products/
    products = Products.objects.all()
    serializer = SzProducts(products, many=True)
    # print(f">>>>>>>>>{serializer}")
    return Response({'data': serializer.data})

# To get specific product.
@api_view(['GET'])
def get_one_product(request, pk): # api/products/one-product/<id-frontend>
    the_product = get_object_or_404(Products, id=pk)
    serializer = SzProducts(the_product, many=False)
    return Response({'data': serializer.data})

# To get products with filter 
@api_view(['GET'])
def get_filtered_products(request):
    products = Products.objects.all()
    filterset = ProductFilters(request.GET, products.order_by("id"))
    serializer = SzProducts(filterset.qs, many=True)
    return Response({'data': serializer.data})

# To get products with filter and seperate to pages
@api_view(['GET'])
def get_filtered_pages(request):
    products = Products.objects.all()
    filterset = ProductFilters(request.GET, products.order_by("id"))
    paginator = PageNumberPagination()
    paginator.page_size = 2  # Set the number of items per page
    paginated_queryset = paginator.paginate_queryset(filterset.qs, request)
    serializer = SzProducts(paginated_queryset, many=True)
    return paginator.get_paginated_response({'data': serializer.data})

# Add product
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_product(request):
    data = request.data
    data['user'] = request.user.id
    get_serializer = SzProducts(data=data)
    if get_serializer.is_valid():
        product = get_serializer.save(user=request.user)
        post_serializer = SzProducts(product, many=False)
        return Response({'product': post_serializer.data})
    else:
        return Response(get_serializer.errors)

# update product
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_product(request, pk):
    product = get_object_or_404(Products, id=pk)
    if product.user != request.user:
        return Response({'error':'you dont have permission to edit this item'}, status= status.HTTP_403_FORBIDDEN)
    else:
        product.name = request.data['name']
        product.description = request.data['description']
        product.price = request.data['price']
        product.brand = request.data['brand']
        product.catagory = request.data['catagory']
        product.rating = request.data['rating']
        product.stock = request.data['stock']
        product.save()
        serializer = SzProducts(product, many=False)
        return Response({'data':serializer.data})
    
# DELETE ITEM
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_product(request, pk):
    product = get_object_or_404(Products, id=pk)
    if product.user != request.user:
        return Response({'error':'you dont have permission to edit this item'}, status= status.HTTP_403_FORBIDDEN)
    else:
        product.delete()
        return Response({'result':'The product has been deleted'}, status=status.HTTP_200_OK)

# Add review
# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def add_review(request, pk):
#     user = request.user
#     print(f"request.user >>>>>>>>{user}")
#     product = get_object_or_404(Products, id=pk)
#     data = request.data
#     review = product.reviews.filter(user = user)
#     if data['rating'] <= 0 or data['rating'] > 5:
#         return Response({'warning':'please select between 1:5'}, status=status.HTTP_400_BAD_REQUEST)
#     elif review.exists():
#         new_review = {
#             'rating':data['rating']
#             , 'comment':data['comment']
#                         }
#         review.update(**new_review)

#         rating = product.reviews.aggregate(avg_ratings = Avg('rating'))
#         product.ratings = rating['avg_ratings']
#         product.save()
        
#         return Response({'details':'Product review updated'})
#     else:
#         Reviews.objects.create(
#             user = user,
#             product = product,
#             rating = data['rating'],
#             comment = data['comment']
#         )
        
#         rating = product.reviews.aggregate(avg_ratings = Avg('rating'))
#         product.ratings = rating['avg_ratings']
#         product.save()
        
#         return Response({'details':'Add Comment Successful'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_review(request, pk):
    product = get_object_or_404(Products, id=pk)
    user = request.user
    data = request.data
    review = request.data['rating']
    if data['rating'] > 5 or data['rating'] < 1:
        return Response({"Error":"Please rate between 1:5"}, status=status.HTTP_400_BAD_REQUEST)
    # التحقق مما إذا كان المستخدم قد اشترى المنتج
    has_purchased = Order.objects.filter(user=user, product=product).exists()
    if not has_purchased:
        return Response({'error': 'You can only review products you have purchased.'}, status=status.HTTP_403_FORBIDDEN)

    # التحقق من وجود مراجعة سابقة
    if product.reviews.filter(user=user).exists():
        return Response({'error': 'You have already reviewed this product'}, status=status.HTTP_400_BAD_REQUEST)

    serializer = SzReview(data=data)
    if serializer.is_valid():
        serializer.save(user=user, product=product)
        return Response({'message': 'Review added successfully'}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




@api_view(['GET'])
def get_product_reviews(request, pk):
    product = get_object_or_404(Products, id=pk)
    reviews = product.reviews.all()
    serializer = SzReview(reviews, many=True)
    return Response({'reviews': serializer.data})

# delete review
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_review(request, pk):
    review = get_object_or_404(Reviews, id=pk)
    if review.user != request.user:
        return Response({'error': 'You do not have permission to delete this review'}, status=status.HTTP_403_FORBIDDEN)
    else:
        review.delete()
        return Response({'message': 'Review deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

class RecommendedProductsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        recommended_products = get_recommended_products(request.user)
        serializer = ProductSerializer(recommended_products, many=True)
        return Response(serializer.data)




