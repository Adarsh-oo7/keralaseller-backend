from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from store.views import PublicStoreView, PublicStoreListView
from users.views import BuyerProfileView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # User authentication endpoints
    path("user/", include("users.urls")),
    
    # API endpoints for authenticated users
    path('api/buyer/profile/', BuyerProfileView.as_view(), name='buyer-profile'),
    path('api/subscriptions/', include('subscriptions.urls')),
    path('api/chat/', include('chat.urls')),
    path('api/categories/', include('categories.urls')),
    
    # Store management endpoints (for sellers)
    path('api/store/', include('store.urls')),
    
    # Product management endpoints 
    path('api/products/', include('products.urls')),
    
    # Orders management
    # path('api/orders/', include('orders.urls')),  # Uncomment if you have orders app
    
    # Public storefront endpoints
    path('shop/<str:seller_phone>/', PublicStoreView.as_view(), name='public-store-view'),
    path('shops/', PublicStoreListView.as_view(), name='public-store-list'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
