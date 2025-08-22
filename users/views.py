# ==============================================================================
# IMPORTS
# ==============================================================================
import re
import random
from django.db.models import Sum, Count
from django.core.cache import cache
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

from .models import Seller, Buyer, SellerToken
from .serializers import RegisterSellerSerializer, SellerSerializer, BuyerSerializer
from products.models import Product
from orders.models import Order, OrderItem

# ==============================================================================
# CUSTOM PERMISSIONS WITH DEBUG LOGGING
# ==============================================================================
class IsBuyer(permissions.BasePermission):
    """
    Allows access only to authenticated users who are instances of the Buyer model.
    """
    def has_permission(self, request, view):
        print(f"🔍 Permission Debug - User: {request.user}")
        print(f"🔍 Permission Debug - User type: {type(request.user)}")
        print(f"🔍 Permission Debug - Is authenticated: {request.user.is_authenticated}")
        print(f"🔍 Permission Debug - Is Buyer instance: {isinstance(request.user, Buyer)}")
        
        if not request.user or not request.user.is_authenticated:
            print("❌ Permission denied: User not authenticated")
            return False
            
        # Check if the user is a Buyer instance
        is_buyer = isinstance(request.user, Buyer)
        if not is_buyer:
            print(f"❌ Permission denied: User is not a Buyer instance (is {type(request.user)})")
        else:
            print("✅ Permission granted: User is authenticated Buyer")
            
        return is_buyer


class IsSeller(permissions.BasePermission):
    """
    Allows access only to authenticated users who are instances of the Seller model.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return isinstance(request.user, Seller)


# ==============================================================================
# SELLER VIEWS
# ==============================================================================
class SendOTP(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        phone = request.data.get('phone')
        if not phone:
            return Response(
                {"error": "Phone number is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        otp = random.randint(1000, 9999)
        cache.set(f"otp_{phone}", otp, timeout=300)
        print(f"OTP for {phone}: {otp}")
        
        return Response(
            {"message": "OTP sent successfully"}, 
            status=status.HTTP_200_OK
        )


class RegisterSeller(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = RegisterSellerSerializer(data=request.data)
        if serializer.is_valid():
            seller = serializer.save()
            token, _ = SellerToken.objects.get_or_create(user=seller)
            cache.delete(f"otp_{seller.phone}")
            
            return Response({
                "message": "Seller registered successfully",
                "token": token.key,
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginSeller(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        phone = request.data.get('phone')
        password = request.data.get('password')
        
        if not phone or not password:
            return Response(
                {"error": "Phone and password are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = Seller.objects.get(phone=phone)
        except Seller.DoesNotExist:
            return Response(
                {"error": "Invalid credentials"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if user.check_password(password) and user.is_active:
            token, _ = SellerToken.objects.get_or_create(user=user)
            return Response({
                "message": "Login successful", 
                "token": token.key
            }, status=status.HTTP_200_OK)
        
        return Response(
            {"error": "Invalid credentials"}, 
            status=status.HTTP_401_UNAUTHORIZED
        )


@api_view(['GET'])
@permission_classes([IsSeller])
def seller_dashboard(request):
    seller = request.user
    store_profile = seller.store_profile
    
    completed_orders = Order.objects.filter(store=store_profile, status='DELIVERED')
    total_revenue = completed_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_orders = Order.objects.filter(store=store_profile).count()
    total_products = Product.objects.filter(store=store_profile).count()
    
    top_products_query = OrderItem.objects.filter(
        order__store=store_profile
    ).values('product__name').annotate(
        total_sold=Sum('quantity')
    ).order_by('-total_sold')[:5]
    
    analytics_data = {
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'total_products': total_products,
        'top_selling_products': list(top_products_query)
    }
    
    serializer = SellerSerializer(seller)
    
    return Response({
        "message": "Seller Dashboard Data",
        "seller": serializer.data,
        "analytics": analytics_data,
    }, status=status.HTTP_200_OK)


# ==============================================================================
# BUYER VIEWS WITH DEBUG LOGGING
# ==============================================================================
class GoogleLoginView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        full_name = request.data.get('name')
        
        print(f"🔍 Login Debug - Email: {email}")
        print(f"🔍 Login Debug - Name: {full_name}")
        
        if not email:
            return Response(
                {'error': 'Email is required.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        buyer, created = Buyer.objects.get_or_create(
            email=email, 
            defaults={'full_name': full_name}
        )
        
        print(f"🔍 Login Debug - Buyer: {buyer}")
        print(f"🔍 Login Debug - Buyer type: {type(buyer)}")
        print(f"🔍 Login Debug - Buyer ID: {buyer.id}")
        print(f"🔍 Login Debug - Created: {created}")
        
        refresh = RefreshToken.for_user(buyer)
        access_token = str(refresh.access_token)
        
        print(f"🔍 Login Debug - Generated token: {access_token[:50]}...")
        
        return Response({
            'message': 'Login successful',
            'token': access_token
        }, status=status.HTTP_200_OK)


class SendBuyerOTP(APIView):
    permission_classes = [IsBuyer]
    
    def post(self, request):
        phone = request.data.get('phone') or request.data.get('phone_number')
        
        if not phone:
            return Response(
                {'error': 'Phone number is required.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Validate phone number format
        phone = str(phone).strip()
        if not re.match(r'^\d{10}$', phone):
            return Response(
                {'error': 'Please enter a valid 10-digit phone number.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Update user's phone number
        request.user.phone_number = phone
        request.user.save()
        
        # Generate and store OTP
        otp = random.randint(1000, 9999)
        cache.set(f"otp_buyer_{request.user.id}", otp, timeout=300)
        
        print(f"OTP for buyer {request.user.email}: {otp}")
        
        return Response({
            'message': 'OTP sent successfully.'
        }, status=status.HTTP_200_OK)


class VerifyBuyerOTP(APIView):
    permission_classes = [IsBuyer]
    
    def post(self, request):
        otp_entered = request.data.get('otp')
        
        if not otp_entered:
            return Response(
                {'error': 'OTP is required.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Validate OTP format
        if not re.match(r'^\d{4}$', str(otp_entered)):
            return Response(
                {'error': 'Please enter a valid 4-digit OTP.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Check stored OTP
        stored_otp = cache.get(f"otp_buyer_{request.user.id}")
        
        if not stored_otp:
            return Response(
                {'error': 'OTP has expired. Please request a new one.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if str(otp_entered) == str(stored_otp):
            # Mark phone as verified
            request.user.phone_verified = True
            request.user.save()
            
            # Clear the OTP from cache
            cache.delete(f"otp_buyer_{request.user.id}")
            
            return Response({
                'message': 'Phone number verified successfully.'
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': 'Invalid OTP. Please try again.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class BuyerProfileView(APIView):
    permission_classes = [IsBuyer]

    def get(self, request):
        """Get the current buyer's profile information."""
        try:
            print(f"🔍 Profile Debug - Request user: {request.user}")
            print(f"🔍 Profile Debug - User type: {type(request.user)}")
            print(f"🔍 Profile Debug - User ID: {getattr(request.user, 'id', 'No ID')}")
            print(f"🔍 Profile Debug - User email: {getattr(request.user, 'email', 'No email')}")
            print(f"🔍 Profile Debug - Is Buyer: {isinstance(request.user, Buyer)}")
            
            serializer = BuyerSerializer(request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"❌ Profile Error: {e}")
            print(f"❌ Profile Error Type: {type(e)}")
            return Response(
                {'error': f'Failed to fetch profile: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def patch(self, request):
        """Update the buyer's profile information (partial update allowed)."""
        try:
            buyer = request.user
            print(f"🔍 Profile Update - User: {buyer}")
            
            serializer = BuyerSerializer(buyer, data=request.data, partial=True)
            
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                print(f"❌ Serializer errors: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"❌ Profile Update Error: {e}")
            return Response(
                {'error': f'Failed to update profile: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
