# In store/views.py

from rest_framework import viewsets, permissions
from .models import Product
from .serializers import ProductSerializer

class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Return only products owned by the currently logged-in seller
        # This assumes you have a signal or logic to create a StoreProfile on seller registration
        return Product.objects.filter(store__seller=self.request.user)

    def perform_create(self, serializer):
        # Automatically assign the seller's store when creating a new product
        serializer.save(store=self.request.user.store_profile)