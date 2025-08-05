# ==============================================================================
# IMPORTS
# ==============================================================================
import random
from django.db.models import Sum, Count
from django.core.cache import cache
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Seller, Buyer, SellerToken
from .serializers import RegisterSellerSerializer, SellerSerializer, BuyerSerializer
from store.models import Product
from orders.models import Order, OrderItem

# ==============================================================================
# CUSTOM PERMISSIONS
# ==============================================================================
class IsBuyer(permissions.BasePermission):
    """
    Allows access only to authenticated users who are instances of the Buyer model.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and isinstance(request.user, Buyer)

# ==============================================================================
# SELLER VIEWS
# ==============================================================================
class SendOTP(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        phone = request.data.get('phone')
        if not phone:
            return Response({"error": "Phone number is required"}, status=status.HTTP_400_BAD_REQUEST)
        otp = random.randint(1000, 9999)
        cache.set(f"otp_{phone}", otp, timeout=300)
        print(f"OTP for {phone}: {otp}")
        return Response({"message": "OTP sent successfully"}, status=status.HTTP_200_OK)

class RegisterSeller(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        serializer = RegisterSellerSerializer(data=request.data)
        if serializer.is_valid():
            seller = serializer.save()
            # ✅ Use the new SellerToken model
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
            return Response({"error": "Phone and password are required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = Seller.objects.get(phone=phone)
        except Seller.DoesNotExist:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        
        if user.check_password(password) and user.is_active:
            # ✅ Use the new SellerToken model
            token, _ = SellerToken.objects.get_or_create(user=user)
            return Response({ "message": "Login successful", "token": token.key }, status=status.HTTP_200_OK)
        
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def seller_dashboard(request):
    seller = request.user
    store_profile = seller.store_profile
    completed_orders = Order.objects.filter(store=store_profile, status='DELIVERED')
    total_revenue = completed_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_orders = Order.objects.filter(store=store_profile).count()
    total_products = Product.objects.filter(store=store_profile).count()
    top_products_query = OrderItem.objects.filter(order__store=store_profile).values('product__name').annotate(total_sold=Sum('quantity')).order_by('-total_sold')[:5]
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
# BUYER VIEWS
# ==============================================================================
class GoogleLoginView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        email = request.data.get('email')
        full_name = request.data.get('name')
        if not email:
            return Response({'error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)
        buyer, created = Buyer.objects.get_or_create(email=email, defaults={'full_name': full_name})
        refresh = RefreshToken.for_user(buyer)
        access_token = str(refresh.access_token)
        return Response({ 'message': 'Login successful', 'token': access_token }, status=status.HTTP_200_OK)

class SendBuyerOTP(APIView):
    permission_classes = [IsBuyer] # ✅ Correctly defined once
    def post(self, request):
        phone = request.data.get('phone')
        if not phone:
            return Response({'error': 'Phone number required.'}, status=status.HTTP_400_BAD_REQUEST)
        request.user.phone_number = phone
        request.user.save()
        otp = random.randint(1000, 9999)
        cache.set(f"otp_buyer_{request.user.id}", otp, timeout=300)
        print(f"OTP for buyer {request.user.email}: {otp}")
        return Response({'message': 'OTP sent.'})

class VerifyBuyerOTP(APIView):
    permission_classes = [IsBuyer] # ✅ Correctly defined once
    def post(self, request):
        otp_entered = request.data.get('otp')
        stored_otp = cache.get(f"otp_buyer_{request.user.id}")
        if str(otp_entered) == str(stored_otp):
            request.user.phone_verified = True
            request.user.save()
            cache.delete(f"otp_buyer_{request.user.id}")
            return Response({'message': 'Phone number verified successfully.'})
        return Response({'error': 'Invalid OTP.'}, status=status.HTTP_400_BAD_REQUEST)

# In users/views.py
class BuyerProfileView(APIView):
    permission_classes = [IsBuyer]

    def get(self, request):
        serializer = BuyerSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        """
        Allows the buyer to update their profile information (e.g., address).
        """
        buyer = request.user
        # partial=True allows for updating only some fields at a time
        serializer = BuyerSerializer(buyer, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)