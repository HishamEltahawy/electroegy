from django.contrib import admin
from django.urls import path, include, re_path
from ProductsApp import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('', views.main, name='main'),
    # Authentication paths
    path('api-auth/', include('rest_framework.urls')),
    path('api/accounts', include('AccountsApp.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # Djoser 
    re_path(r'^auth/', include('djoser.urls')),  # إدارة المستخدمين (^auth << this mean link start with auth)
    re_path(r'^auth/', include('djoser.urls.authtoken')),  
    re_path(r'^auth/', include('djoser.urls.jwt')),  # نقاط نهاية لـ JWT
    # Admin path
    path('admin/', admin.site.urls),
    # Apps paths
    path('api/products/', include('ProductsApp.urls')),
    path('api/accounts/', include('AccountsApp.urls')),
    path('api/orders/', include('OrdersApp.urls')),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# These working on error_view.py file for back message Json response for errors 404 and 500
handler404 = 'utils.error_view.handler_404'
handler500 = 'utils.error_view.handler_500'