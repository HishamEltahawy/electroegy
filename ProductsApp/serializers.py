from rest_framework import serializers
from .models import Products, Reviews

class SzReview(serializers.ModelSerializer):
    user = serializers.StringRelatedField()  # عرض اسم المستخدم بدلاً من الـ ID
    product = serializers.StringRelatedField()  # عرض اسم المنتج بدلاً من الـ ID
    class Meta:
        model = Reviews
        fields = '__all__'

class SzProducts(serializers.ModelSerializer):
    reviews = serializers.SerializerMethodField(method_name='get_reviews', read_only=True)
    publisher = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Products
        # fields = '__all__'
        fields = ['id', 'name', 'image', 'description', 'price', 'brand', 'category', 'rating', 'stock', 'created_at', 'publisher', 'reviews']
        read_only_fields = ['id'] 
    def get_reviews(self, obj):
        reviews = obj.reviews.all()
        serializer = SzReview(reviews, many=True)
        return serializer.data
