# In store/views.py

from rest_framework import viewsets, permissions
from .models import Product
from .serializers import ProductSerializer, StoreProfileSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

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




class StoreProfileView(APIView):
    """
    Manages the store profile for the authenticated seller.
    - GET: Retrieve the current store profile.
    - PATCH: Update the store profile.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Retrieve the store profile linked to the logged-in seller
        store_profile = request.user.store_profile
        # Pass context to get the full URL for the image
        serializer = StoreProfileSerializer(store_profile, context={'request': request})
        return Response(serializer.data)

    def patch(self, request):
        store_profile = request.user.store_profile
        # 'partial=True' allows for partial updates (e.g., only changing the name)
        serializer = StoreProfileSerializer(
            store_profile, data=request.data, partial=True, context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
