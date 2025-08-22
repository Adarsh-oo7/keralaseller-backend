from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
import razorpay

from .models import StoreProfile
from .serializers import StoreProfileSerializer
from products.serializers import ProductSerializer
from django.conf import settings
from products.models import Product # Import Product from the products app
from users.models import Seller

# ==============================================================================
# PAGINATION
# ==============================================================================
class StorePagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 50

# ==============================================================================
# SELLER DASHBOARD VIEWS
# ==============================================================================
class StoreProfileView(APIView):
    """
    Manages the store profile for the currently authenticated seller.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = StoreProfileSerializer(request.user.store_profile, context={'request': request})
        return Response(serializer.data)

    def patch(self, request):
        store_profile = request.user.store_profile
        serializer = StoreProfileSerializer(store_profile, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            # Your Razorpay key verification logic can be added here
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ==============================================================================
# PUBLIC-FACING VIEWS
# ==============================================================================
class PublicStoreListView(ListAPIView):
    """
    Provides a public, paginated list of all active store profiles.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = StoreProfileSerializer
    pagination_class = StorePagination
    queryset = StoreProfile.objects.filter(seller__is_active=True).order_by('-created_at')
    filter_backends = [SearchFilter]
    search_fields = ['name', 'tagline']

class PublicStoreView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, seller_phone=None):
        try:
            seller = Seller.objects.get(phone=seller_phone)
            store_profile = seller.store_profile
            
            products = Product.objects.filter(
                store=store_profile, is_active=True, online_stock__gt=0,
                sale_type__in=[Product.SaleType.ONLINE_AND_OFFLINE, Product.SaleType.ONLINE_ONLY]
            ).order_by('-created_at')

            # Ensure context is passed to both serializers
            store_data = StoreProfileSerializer(store_profile, context={'request': request}).data
            product_data = ProductSerializer(products, many=True, context={'request': request}).data
            
            print(f"🔍 Store serialized data: {store_data}")  # Debug
            print(f"🔍 Products count: {len(product_data)}")  # Debug
            if product_data:
                print(f"🔍 First product main_image_url: {product_data[0].get('main_image_url')}")  # Debug

            # Automatic SEO Generation
            if not store_data.get('meta_title'):
                store_data['meta_title'] = f"{store_profile.name} | Kerala Sellers"
            if not store_data.get('meta_description'):
                store_data['meta_description'] = f"Explore products from {store_profile.name} on Kerala Sellers."

            return Response({'store': store_data, 'products': product_data})
        except (Seller.DoesNotExist, StoreProfile.DoesNotExist):
            return Response({'error': 'Store not found.'}, status=status.HTTP_404_NOT_FOUND)
