from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Product, StoreProfile
from .serializers import ProductSerializer, StoreProfileSerializer
import razorpay
from rest_framework.filters import SearchFilter # ✅ Add this import

class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [SearchFilter]
    search_fields = ['name', 'model_name']

    def get_serializer_context(self):
        """
        Ensures the serializer has access to the request context,
        which is needed to build full absolute URLs for images.
        """
        return {'request': self.request}

    def get_queryset(self):
        # For an authenticated seller, show all their products in the dashboard
        if self.request.user.is_authenticated and hasattr(self.request.user, 'store_profile'):
             return Product.objects.filter(store__seller=self.request.user)
        
        # For the public, only show active, online products with stock
        return Product.objects.filter(
            is_active=True, 
            online_stock__gt=0,
            sale_type__in=[Product.SaleType.ONLINE_AND_OFFLINE, Product.SaleType.ONLINE_ONLY]
        ).order_by('-created_at')

    def perform_create(self, serializer):
        # Pass the current user to be used in the signal
        serializer.save(
            store=self.request.user.store_profile,
            _current_user=self.request.user 
        )



class StoreProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        store_profile = request.user.store_profile
        serializer = StoreProfileSerializer(store_profile, context={'request': request})
        return Response(serializer.data)

    def patch(self, request):
        store_profile = request.user.store_profile
        
        key_id = request.data.get('razorpay_key_id')
        key_secret = request.data.get('razorforpay_key_secret')

        if request.data.get('payment_method') == 'RAZORPAY' and key_id and key_secret:
            try:
                client = razorpay.Client(auth=(key_id, key_secret))
                client.payment.all({'count': 1})
            except Exception as e:
                error_message = str(e).lower()
                if 'authentication failed' in error_message or 'bad credentials' in error_message:
                    return Response(
                        {"error": "Invalid Razorpay Key ID or Key Secret. Please check again."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                else:
                    return Response(
                        {"error": "Could not verify Razorpay keys. Please try again later."},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
        
        serializer = StoreProfileSerializer(
            store_profile, data=request.data, partial=True, context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# In store/views.py
class UpdateStockView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk=None):
        try:
            product = Product.objects.get(pk=pk, store__seller=request.user)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)

        # ✅ Get the note from the request data
        note = request.data.get('note', '')

        if 'total_stock' in request.data:
            total_stock = request.data['total_stock']
            if isinstance(total_stock, int) and total_stock >= 0:
                product.total_stock = total_stock
            else:
                return Response({'error': 'Invalid total_stock value.'}, status=status.HTTP_400_BAD_REQUEST)

        if 'online_stock' in request.data:
            online_stock = request.data['online_stock']
            if isinstance(online_stock, int) and online_stock >= 0:
                product.online_stock = online_stock
            else:
                return Response({'error': 'Invalid online_stock value.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # ✅ Attach the user and note to the instance before saving
            # This allows the signal to access them
            product._current_user = request.user
            product._stock_change_note = note
            product.save()
        except Exception:
            return Response({'error': 'Online stock cannot be greater than total stock.'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'success': True,
            'total_stock': product.total_stock,
            'online_stock': product.online_stock
        }, status=status.HTTP_200_OK)
    
# In store/views.py
from .models import StockHistory
from .serializers import StockHistorySerializer
from rest_framework.generics import ListAPIView
class StockHistoryListView(ListAPIView):
    serializer_class = StockHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Return history for products belonging to the seller's store
        return StockHistory.objects.filter(product__store__seller=self.request.user).order_by('-timestamp')



class PublicStoreListView(ListAPIView):
    """
    Provides a public list of all active store profiles.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = StoreProfileSerializer
    queryset = StoreProfile.objects.filter(seller__is_active=True).order_by('-created_at')


from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.filters import SearchFilter
from rest_framework.generics import ListAPIView
from .models import Product, StoreProfile, StockHistory
from .serializers import ProductSerializer, StoreProfileSerializer, StockHistorySerializer
from users.models import Seller # Make sure Seller is imported

# This is your existing viewset for the seller dashboard
class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [SearchFilter]
    search_fields = ['name', 'model_name']

    def get_serializer_context(self):
        return {'request': self.request}

    def get_queryset(self):
        if self.request.user.is_authenticated and hasattr(self.request.user, 'store_profile'):
             return Product.objects.filter(store__seller=self.request.user)
        
        return Product.objects.filter(
            is_active=True, 
            online_stock__gt=0,
            sale_type__in=[Product.SaleType.ONLINE_AND_OFFLINE, Product.SaleType.ONLINE_ONLY]
        ).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(store=self.request.user.store_profile)

# ... (Your other existing views like StoreProfileView, UpdateStockView, etc., are here) ...


# ✅ Add this new view for the public storefront
class PublicStoreView(APIView):
    """
    Provides the public data for a single seller's storefront,
    accessible via a unique identifier like the seller's phone number.
    """
    permission_classes = [permissions.AllowAny] # This makes the view public

    def get(self, request, seller_phone=None):
        try:
            seller = Seller.objects.get(phone=seller_phone)
            store_profile = seller.store_profile
            
            products = Product.objects.filter(
                store=store_profile,
                is_active=True,
                online_stock__gt=0,
                sale_type__in=[Product.SaleType.ONLINE_AND_OFFLINE, Product.SaleType.ONLINE_ONLY]
            ).order_by('-created_at')

            store_data = StoreProfileSerializer(store_profile, context={'request': request}).data
            product_data = ProductSerializer(products, many=True, context={'request': request}).data

            return Response({
                'store': store_data,
                'products': product_data
            })

        except (Seller.DoesNotExist, StoreProfile.DoesNotExist):
            return Response({'error': 'Store not found.'}, status=status.HTTP_404_NOT_FOUND)
