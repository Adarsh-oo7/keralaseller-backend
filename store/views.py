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
        """
        Save the product with the seller's store and set the current user for the signal.
        """
        # Get the seller (current user)
        seller = self.request.user
        
        # Save the product with the store
        product = serializer.save(store=seller.store_profile)
        
        # Set the current user for the signal to use
        product._current_user = seller
        product._stock_change_note = "Product created via dashboard"
        
        # Save again to trigger the post_save signal with user info
        product.save()
        
        return product

    def perform_update(self, serializer):
        """
        Update the product and set the current user for stock tracking.
        """
        seller = self.request.user
        
        # Save the product
        product = serializer.save()
        
        # Set the current user and note for the signal
        product._current_user = seller
        product._stock_change_note = "Product updated via dashboard"
        
        # Save again to trigger the signal with user info
        product.save()
        
        return product

        # Let's update the signal for a more robust solution.


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

from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import ListAPIView
class StorePagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 50

class PublicStoreListView(ListAPIView):
    """
    Provides a public, paginated list of all active store profiles.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = StoreProfileSerializer
    pagination_class = StorePagination # Assuming you have this
    queryset = StoreProfile.objects.filter(seller__is_active=True).order_by('-created_at')
    
    # ✅ Add these two lines to enable searching
    filter_backends = [SearchFilter]
    search_fields = ['name', 'tagline', 'description'] # 
    
    def get_queryset(self):
        return StoreProfile.objects.filter(seller__is_active=True).order_by('-created_at')


from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.filters import SearchFilter
from rest_framework.generics import ListAPIView
from .models import Product, StoreProfile, StockHistory
from .serializers import ProductSerializer, StoreProfileSerializer, StockHistorySerializer
from users.models import Seller # Make sure Seller is imported

# This is your existing viewset for the seller dashboard
# class ProductViewSet(viewsets.ModelViewSet):
#     serializer_class = ProductSerializer
#     permission_classes = [permissions.IsAuthenticatedOrReadOnly]
#     filter_backends = [SearchFilter]
#     search_fields = ['name', 'model_name']

#     def get_serializer_context(self):
#         return {'request': self.request}

#     def get_queryset(self):
#         if self.request.user.is_authenticated and hasattr(self.request.user, 'store_profile'):
#              return Product.objects.filter(store__seller=self.request.user)
        
#         return Product.objects.filter(
#             is_active=True, 
#             online_stock__gt=0,
#             sale_type__in=[Product.SaleType.ONLINE_AND_OFFLINE, Product.SaleType.ONLINE_ONLY]
#         ).order_by('-created_at')

#     def perform_create(self, serializer):
#         """
#         Assigns the store and passes the current user to the model
#         before creating a new product.
#         """
#         # Pass the current user to be used in the signal
#         serializer.save(
#             store=self.request.user.store_profile,
#             _current_user=self.request.user 
#         )
# ... (Your other existing views like StoreProfileView, UpdateStockView, etc., are here) ...


# ✅ Add this new view for the public storefront

class PublicStoreView(APIView):
    """
    Provides the public data for a single seller's storefront.
    Automatically generates SEO meta tags if they are not provided by the seller.
    """
    permission_classes = [permissions.AllowAny]

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

            # ✅ START: Automatic SEO Generation
            # If the seller has not provided a custom SEO title, create one.
            if not store_data.get('meta_title'):
                store_data['meta_title'] = f"{store_profile.name} | Kerala Sellers"
            
            # If the seller has not provided a custom SEO description, create one.
            if not store_data.get('meta_description'):
                store_data['meta_description'] = f"Explore unique products from {store_profile.name}, a local business on the Kerala Sellers platform. Order online today."
            # ✅ END: Automatic SEO Generation

            return Response({
                'store': store_data,
                'products': product_data
            })

        except (Seller.DoesNotExist, StoreProfile.DoesNotExist):
            return Response({'error': 'Store not found.'}, status=status.HTTP_404_NOT_FOUND)

from datetime import date, timedelta
class EstimateDeliveryView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk=None):
        product = Product.objects.get(pk=pk)
        store = product.store
        buyer_pincode = request.query_params.get('pincode')

        if not store.pincode or not buyer_pincode:
            return Response({'estimate': 'Delivery info not available.'})

        # Simple logic for Kerala (pincodes starting with '6')
        is_local = buyer_pincode.startswith('6')
        
        # ✅ START: Hybrid Logic
        # 1. Check for seller's manual estimate first
        if is_local and store.delivery_time_local:
            estimate = f"Around {store.delivery_time_local}"
        elif not is_local and store.delivery_time_national:
            estimate = f"Around {store.delivery_time_national}"
        else:
            # 2. Fallback to automatic calculation
            delivery_days = 3 if is_local else 7
            today = date.today()
            estimated_date = today + timedelta(days=delivery_days)
            estimate = f"By {estimated_date.strftime('%A, %b %d')}"
        # ✅ END: Hybrid Logic
        
        return Response({'estimate': estimate})



from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from .models import Review
from .serializers import ReviewSerializer
from orders.models import Order
from users.views import IsBuyer # Assuming IsBuyer is in users/views.py

# ... (your other views in this file) ...


class CreateReviewView(APIView):
    """
    Allows a verified buyer to create a review for a product
    they have purchased and had delivered.
    """
    permission_classes = [IsBuyer]

    def post(self, request, pk=None):
        product_id = pk
        buyer = request.user
        
        # Verification Logic: Check if the buyer has purchased this product
        has_purchased = Order.objects.filter(
            buyer=buyer,
            status=Order.OrderStatus.DELIVERED,
            items__product_id=product_id
        ).exists()

        if not has_purchased:
            return Response(
                {'error': 'You can only review products you have purchased and received.'}, 
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if a review already exists
        if Review.objects.filter(product_id=product_id, buyer=buyer).exists():
            return Response({'error': 'You have already reviewed this product.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ReviewSerializer(data=request.data)
        if serializer.is_valid():
            # Associate the review with the product and the buyer
            serializer.save(product_id=product_id, buyer=buyer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)