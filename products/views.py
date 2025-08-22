from datetime import date, timedelta
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.filters import SearchFilter
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404

from .models import Product, ProductImage, Review, StockHistory
from .serializers import (
    ProductSerializer, 
    StockHistorySerializer,
    ReviewSerializer
)
from users.models import Seller, Buyer
from users.views import IsBuyer
from orders.models import Order


# ==============================================================================
# PAGINATION & MAIN PRODUCT VIEWSET
# ==============================================================================
class ProductPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 50


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = ProductPagination
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ['name', 'model_name', 'description']
    filterset_fields = ['category', 'sale_type', 'is_active']

    def get_serializer_context(self):
        """Enhanced context with additional data."""
        context = super().get_serializer_context()
        context.update({
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        })
        return context

    def get_queryset(self):
        """Return filtered queryset based on user type."""
        user = self.request.user
        if user.is_authenticated and isinstance(user, Seller):
            # For seller dashboard - show all their products
            return Product.objects.filter(
                store__seller=user
            ).select_related('store', 'category').prefetch_related('sub_images', 'reviews')
        
        # For public/buyer view - only active products with stock
        return Product.objects.filter(
            is_active=True, 
            online_stock__gt=0,
            sale_type__in=[Product.SaleType.ONLINE_AND_OFFLINE, Product.SaleType.ONLINE_ONLY]
        ).select_related('store', 'category').prefetch_related('sub_images', 'reviews').order_by('-created_at')

    def perform_create(self, serializer):
        """Create product with sub-images."""
        sub_images_data = self.request.FILES.getlist('sub_images')
        
        # Save the main product
        instance = serializer.save(
            store=self.request.user.store_profile
        )
        
        # Create sub-images using bulk_create for better performance
        if sub_images_data:
            sub_images = [
                ProductImage(product=instance, image=image_data) 
                for image_data in sub_images_data
            ]
            ProductImage.objects.bulk_create(sub_images)

    def perform_update(self, serializer):
        """Update product and handle sub-images."""
        sub_images_data = self.request.FILES.getlist('sub_images')
        instance = serializer.save()
        
        # Add new sub-images if provided (existing ones remain)
        if sub_images_data:
            sub_images = [
                ProductImage(product=instance, image=image_data) 
                for image_data in sub_images_data
            ]
            ProductImage.objects.bulk_create(sub_images)

    def perform_destroy(self, instance):
        """Clean up image files when deleting product."""
        # Delete image files from disk to free up space
        if instance.main_image:
            instance.main_image.delete(save=False)
        for sub_image in instance.sub_images.all():
            if sub_image.image:
                sub_image.image.delete(save=False)
        super().perform_destroy(instance)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def toggle_active(self, request, pk=None):
        """Toggle product active status (seller only)."""
        product = get_object_or_404(Product, pk=pk, store__seller=request.user)
        product.is_active = not product.is_active
        product.save()
        return Response({
            'success': True,
            'is_active': product.is_active,
            'message': f'Product {"activated" if product.is_active else "deactivated"} successfully'
        })

    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        """Get all reviews for a product."""
        product = self.get_object()
        reviews = product.reviews.all().order_by('-created_at')
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)


# ==============================================================================
# STOCK MANAGEMENT VIEWS
# ==============================================================================
class UpdateStockView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def patch(self, request, pk=None):
        try:
            product = Product.objects.get(pk=pk, store__seller=request.user)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        note = request.data.get('note', '')
        total_stock = request.data.get('total_stock')
        online_stock = request.data.get('online_stock')
        
        # Validate stock values
        try:
            if total_stock is not None:
                product.total_stock = int(total_stock)
            if online_stock is not None:
                product.online_stock = int(online_stock)
                
            # Validate business logic
            if product.online_stock > product.total_stock:
                return Response({
                    'error': 'Online stock cannot be greater than total stock.'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except (ValueError, TypeError):
            return Response({
                'error': 'Stock values must be valid integers.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            product._current_user = request.user
            product._stock_change_note = note
            product.save()
        except Exception as e:
            return Response({
                'error': f'Failed to update stock: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        return Response({
            'success': True, 
            'total_stock': product.total_stock, 
            'online_stock': product.online_stock,
            'message': 'Stock updated successfully'
        })


class StockHistoryListView(ListAPIView):
    serializer_class = StockHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = ProductPagination
    
    def get_queryset(self):
        return StockHistory.objects.filter(
            product__store__seller=self.request.user
        ).select_related('product', 'user').order_by('-timestamp')


# ==============================================================================
# REVIEW VIEWS
# ==============================================================================
class ReviewListView(ListAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = ProductPagination
    
    def get_queryset(self):
        product_id = self.kwargs['pk']
        return Review.objects.filter(
            product_id=product_id
        ).select_related('buyer').order_by('-created_at')


class CreateReviewView(APIView):
    permission_classes = [IsBuyer]
    
    def post(self, request, pk=None):
        product_id = pk
        buyer = request.user
        
        # Check if user has purchased the product
        has_purchased = Order.objects.filter(
            buyer=buyer, 
            status=Order.OrderStatus.DELIVERED, 
            items__product_id=product_id
        ).exists()
        
        if not has_purchased:
            return Response({
                'error': 'You can only review products you have purchased and received.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if user already reviewed this product
        if Review.objects.filter(product_id=product_id, buyer=buyer).exists():
            return Response({
                'error': 'You have already reviewed this product.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate and create review
        serializer = ReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(product_id=product_id, buyer=buyer)
            return Response({
                'success': True,
                'message': 'Review created successfully',
                'review': serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'error': 'Invalid review data',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class CanReviewView(APIView):
    permission_classes = [IsBuyer]
    
    def get(self, request, pk=None):
        has_purchased = Order.objects.filter(
            buyer=request.user,
            status=Order.OrderStatus.DELIVERED,
            items__product_id=pk
        ).exists()
        
        already_reviewed = Review.objects.filter(
            product_id=pk, 
            buyer=request.user
        ).exists()
        
        return Response({
            'can_review': has_purchased and not already_reviewed,
            'has_purchased': has_purchased,
            'already_reviewed': already_reviewed
        })


# ==============================================================================
# PUBLIC UTILITY VIEWS
# ==============================================================================
class EstimateDeliveryView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, pk=None):
        try:
            product = Product.objects.select_related('store').get(pk=pk)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)
            
        store = product.store
        buyer_pincode = request.query_params.get('pincode')
        
        if not buyer_pincode:
            return Response({
                'error': 'Pincode is required for delivery estimation.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not store.pincode:
            return Response({
                'estimate': 'Delivery information not available for this store.'
            })
        
        # Simple logic for Kerala (pincode starting with 6)
        is_local = buyer_pincode.startswith('6') and store.pincode.startswith('6')
        
        if is_local and store.delivery_time_local:
            estimate = f"Around {store.delivery_time_local}"
        elif not is_local and store.delivery_time_national:
            estimate = f"Around {store.delivery_time_national}"
        else:
            # Default estimation
            delivery_days = 3 if is_local else 7
            estimated_date = date.today() + timedelta(days=delivery_days)
            estimate = f"By {estimated_date.strftime('%A, %b %d')}"
        
        return Response({
            'estimate': estimate,
            'is_local_delivery': is_local,
            'store_location': store.pincode
        })
