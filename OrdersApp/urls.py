from django.urls import path
from . import views
from .views import OrderStatusView

urlpatterns = [
    # Cart API Endpoints
    path('cart/', views.CartView.as_view(), name='cart'),
    path('cart/items/', views.CartItemView.as_view(), name='cart_items'),
    path('cart/items/<uuid:product_id>/', views.CartItemView.as_view(), name='remove_cart_item'),
    
    # Order API Endpoints
    path('orders/', views.OrderListView.as_view(), name='order_list'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('orders/create/', views.CreateOrderView.as_view(), name='create_order'),
    path('orders/<int:pk>/update-status/', views.UpdateOrderStatusView.as_view(), name='update_order_status'),
    path('orders/<int:pk>/cancel/', views.CancelOrderView.as_view(), name='cancel_order'),
    path('order/<int:order_id>/status/', OrderStatusView.as_view(), name='order-status'),
    
    # Review API Endpoint
    path('reviews/create/', views.CreateProductReviewView.as_view(), name='create_product_review'),
    
    # Legacy endpoints for backward compatibility
    # path('new_order/', views.new_order, name='new_order'), 
    # path('get_all_orders/', views.get_all_orders, name='get_all_orders'), 
    # path('get_one_order/<str:pk>/', views.get_one_order, name='get_one_order'), 
    # path('process_order/<str:pk>/process/', views.process_order, name='process_order'), 
    # path('delete_order/<str:pk>/delete/', views.delete_order, name='delete_order'), 
    # path('add_to_cart/', views.add_to_cart, name='add_to_cart'),
    # path('remove_cart_item/<str:product_id>/', views.remove_from_cart, name='remove_from_cart'),
]