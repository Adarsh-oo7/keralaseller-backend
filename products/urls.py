# products/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProductViewSet, 
    UpdateStockView, 
    StockHistoryListView,
    ReviewListView, 
    CreateReviewView,
    CanReviewView,
    EstimateDeliveryView
)

router = DefaultRouter()
router.register(r'', ProductViewSet, basename='product')

urlpatterns = [
    path('<int:pk>/update-stock/', UpdateStockView.as_view(), name='update-stock'),
    path('<int:pk>/reviews/', ReviewListView.as_view(), name='product-reviews'),
    path('<int:pk>/create-review/', CreateReviewView.as_view(), name='create-review'),
    path('<int:pk>/can-review/', CanReviewView.as_view(), name='can-review'),
    path('<int:pk>/estimate-delivery/', EstimateDeliveryView.as_view(), name='estimate-delivery'),
    path('stock-history/', StockHistoryListView.as_view(), name='stock-history'),
    path('', include(router.urls)),
]
