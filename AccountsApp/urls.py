from django.urls import path, include
from AccountsApp import views
from .views import WishlistView, Enable2FAView, Disable2FAView, Verify2FAView, Request2FACodeView

urlpatterns = [

    # Apps paths
    # api/accounts/
    path('register/', views.register), # register/
    path('current_user/', views.current_user), # current_user/
    path('update_user/', views.update_user), # update_user/
    path('forget_password/', views.forget_password), # forget_password/
    path('reset_password/<str:token>', views.reset_password), # reset_password/
    path('wishlist/', WishlistView.as_view(), name='wishlist'), # wishlist/
    path('2fa/enable/', Enable2FAView.as_view(), name='enable-2fa'), # 2fa/enable/
    path('2fa/disable/', Disable2FAView.as_view(), name='disable-2fa'), # 2fa/disable/
    path('2fa/verify/', Verify2FAView.as_view(), name='verify-2fa'), # 2fa/verify/
    path('2fa/request-code/', Request2FACodeView.as_view(), name='request-2fa-code'), # 2fa/request-code/
]