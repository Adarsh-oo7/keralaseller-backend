# In store/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, StoreProfileView,UpdateStockView, StockHistoryListView
from orders.views import OrderViewSet # <-- Import the OrderViewSet

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'orders', OrderViewSet, basename='order') # <-- Add the orders endpoint here

urlpatterns = [
    # This is for your settings page
    path('profile/', StoreProfileView.as_view(), name='store-profile'),
    path('products/<int:pk>/update-stock/', UpdateStockView.as_view(), name='update-stock'),
    path('stock-history/', StockHistoryListView.as_view(), name='stock-history'),

    # This now includes both /products/ and /orders/
    path('', include(router.urls)),
]