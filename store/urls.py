# store/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StoreProfileView, PublicStoreListView
from products.views import (
    ProductViewSet, 
    UpdateStockView, 
    StockHistoryListView, 
    CreateReviewView
)

# Create router and register products
router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')

urlpatterns = [
    # Store management
    path('profile/', StoreProfileView.as_view(), name='store-profile'),
    
    # Stock management  
    path('products/<int:pk>/update-stock/', UpdateStockView.as_view(), name='update-stock'),
    path('stock-history/', StockHistoryListView.as_view(), name='stock-history'),
    path('products/<int:pk>/create-review/', CreateReviewView.as_view(), name='create-review'),
    
    # Public store views
    path('shops/', PublicStoreListView.as_view(), name='public-store-list'),
    
    # Include router URLs - this creates /products/ endpoints
    path('', include(router.urls)),
]
