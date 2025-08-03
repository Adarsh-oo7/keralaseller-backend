# In users/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from django.core.cache import cache
from .models import Seller
from .serializers import RegisterSellerSerializer, SellerSerializer
import random

# --- OTP Handling ---
class SendOTP(APIView):
    """
    Generates a 4-digit OTP, prints it for debugging, and stores it in
    the cache for 5 minutes.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        phone = request.data.get('phone')
        if not phone:
            return Response({"error": "Phone number is required"}, status=status.HTTP_400_BAD_REQUEST)

        otp = random.randint(1000, 9999)
        # Store OTP in cache with a 5-minute (300 seconds) timeout
        cache.set(f"otp_{phone}", otp, timeout=300)

        print(f"OTP for {phone}: {otp}") # For development/debugging
        return Response({"message": "OTP sent successfully"}, status=status.HTTP_200_OK)


# --- Authentication Views ---
class RegisterSeller(APIView):
    """
    Handles seller registration using the RegisterSellerSerializer for validation.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSellerSerializer(data=request.data)
        if serializer.is_valid():
            seller = serializer.save()
            token, _ = Token.objects.get_or_create(user=seller)
            cache.delete(f"otp_{seller.phone}") # Clean up OTP after use
            return Response({
                "message": "Seller registered successfully",
                "token": token.key,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginSeller(APIView):
    """
    Handles seller login by directly checking credentials and returning a token.
    """
    permission_classes = [AllowAny]

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
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                "message": "Login successful",
                "token": token.key,
            }, status=status.HTTP_200_OK)

        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)


# --- Dashboard View ---
from django.db.models import Sum, Count
from store.models import Product  # If not already imported
from orders.models import Order, OrderItem

# ... (other imports)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def seller_dashboard(request):
    seller = request.user
    store_profile = seller.store_profile

    # --- Analytics Calculations ---
    completed_orders = Order.objects.filter(store=store_profile, status='DELIVERED')
    
    total_revenue = completed_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_orders = Order.objects.filter(store=store_profile).count()
    total_products = Product.objects.filter(store=store_profile).count()

    # Find top 5 selling products
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
    # --- End Analytics Calculations ---

    serializer = SellerSerializer(seller)
    return Response({
        "message": "Seller Dashboard Data",
        "seller": serializer.data,
        "analytics": analytics_data, # ✅ Add analytics to the response
    }, status=status.HTTP_200_OK)

from django.db.models import Q
from rest_framework.authtoken.models import Token
from users.models import Buyer
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView        
from .models import Buyer
from .serializers import BuyerSerializer # We will create this
from rest_framework.authtoken.models import Token



# This is a conceptual view. A real implementation would use a library
# like 'dj-rest-auth' with 'allauth' for robust Google authentication.
class GoogleLoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        email = request.data.get('email') # Assume frontend sends verified email
        full_name = request.data.get('name')
        if not email:
            return Response({'error': 'Email is required.'}, status=400)
        
        buyer, created = Buyer.objects.get_or_create(
            email=email,
            defaults={'full_name': full_name}
        )
        token, _ = Token.objects.get_or_create(user=buyer)
        return Response({'token': token.key})

class SendBuyerOTP(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        phone = request.data.get('phone')
        if not phone:
            return Response({'error': 'Phone number required.'}, status=400)
        
        # Save phone to user, but not yet verified
        request.user.phone_number = phone
        request.user.save()
        
        otp = random.randint(1000, 9999)
        cache.set(f"otp_buyer_{request.user.id}", otp, timeout=300)
        print(f"OTP for buyer {request.user.email}: {otp}")
        return Response({'message': 'OTP sent.'})

class VerifyBuyerOTP(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        otp_entered = request.data.get('otp')
        stored_otp = cache.get(f"otp_buyer_{request.user.id}")

        if str(otp_entered) == str(stored_otp):
            request.user.phone_verified = True
            request.user.save()
            cache.delete(f"otp_buyer_{request.user.id}")
            return Response({'message': 'Phone number verified successfully.'})
        
        return Response({'error': 'Invalid OTP.'}, status=400)



# ✅ Add this new view for the buyer's profile
class BuyerProfileView(APIView):
    """
    Provides the profile data for the authenticated buyer.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Ensure the logged-in user is a Buyer instance
        if not isinstance(request.user, Buyer):
            return Response({'error': 'User is not a buyer.'}, status=status.HTTP_403_FORBIDDEN)
        
        # Serialize and return the buyer's data
        serializer = BuyerSerializer(request.user)
        return Response(serializer.data)