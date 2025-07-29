# In store/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, StoreProfileView

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')

urlpatterns = [
    path('profile/', StoreProfileView.as_view(), name='store-profile'),

    path('', include(router.urls)),
]