from ProductsApp.models import Products
from django.db.models import Count

def get_recommended_products(user):
    """
    Generate product recommendations based on the most popular products
    or products frequently added to wishlists.
    """
    if not user.is_authenticated:
        return []

    # Get products frequently added to wishlists
    popular_products = Products.objects.annotate(wishlist_count=Count('wishlisted_by')).order_by('-wishlist_count')[:10]

    return popular_products