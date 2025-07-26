from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth import authenticate
from .models import Seller
from .serializers import SellerSerializer
import random
import logging

# ✅ Add logging for debugging
logger = logging.getLogger(__name__)

otp_db = {}  # ✅ Temporary OTP storage (use DB or Redis in production)


from rest_framework.permissions import AllowAny

class SendOTP(APIView):
    """Send OTP to phone"""
    permission_classes = [AllowAny]  # ✅ Allow without auth

    def post(self, request):
        phone = request.data.get('phone')
        if not phone:
            return Response({"error": "Phone number is required"}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Generate OTP (4 digits)
        otp = random.randint(1000, 9999)
        otp_db[phone] = otp

        print(f"✅ OTP sent to {phone}: {otp}")
        return Response({"message": "OTP sent successfully"}, status=status.HTTP_200_OK)



class RegisterSeller(APIView):
    permission_classes = [AllowAny]  # ✅ Add this to allow unauthenticated access

    def post(self, request):
        phone = request.data.get('phone')
        password = request.data.get('password')
        otp = request.data.get('otp')
        name = request.data.get('name')
        shop_name = request.data.get('shop_name')
        email = request.data.get('email')

        print(f"🔍 Registration attempt for phone: {phone}")

        if not otp or otp_db.get(phone) != int(otp):
            return Response({"error": "Invalid OTP"}, status=400)

        if Seller.objects.filter(phone=phone).exists():
            return Response({"error": "Seller already exists"}, status=400)

        seller = Seller.objects.create_user(
            phone=phone,
            password=password,
            name=name,
            shop_name=shop_name,
            email=email
        )
        otp_db.pop(phone, None)

        token, created = Token.objects.get_or_create(user=seller)

        print(f"✅ Seller registered successfully: {phone}")

        return Response({
            "message": "Seller registered successfully",
            "token": token.key,
            "shop_url": f"/shop/{seller.phone}"
        }, status=201)
from django.views.decorators.csrf import csrf_exempt

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

@method_decorator(csrf_exempt, name='dispatch')
class LoginSeller(APIView):
    """Login seller with phone & password"""
    permission_classes = [AllowAny]  # ← Also make sure this is added

    def post(self, request):
        phone = request.data.get('phone')
        password = request.data.get('password')

        print(f"🔍 Login attempt for phone: {phone}")
        print(f"🔍 Password provided: {'Yes' if password else 'No'}")

        if not phone or not password:
            return Response({"error": "Phone and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Check if seller exists first
        try:
            seller = Seller.objects.get(phone=phone)
            print(f"✅ Seller found: {seller.phone}")
            print(f"🔍 Seller is_active: {seller.is_active}")
            print(f"🔍 Password check: {seller.check_password(password)}")
        except Seller.DoesNotExist:
            print(f"❌ Seller not found for phone: {phone}")
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        # ✅ Try authentication
        user = authenticate(request, phone=phone, password=password)
        print(f"🔍 Authentication result: {user}")

        if user and isinstance(user, Seller):
            token, created = Token.objects.get_or_create(user=user)

            print(f"✅ Login successful for: {phone}")
            return Response({
                "message": "Login successful",
                "token": token.key,
                "shop_url": f"/shop/{user.phone}"
            }, status=status.HTTP_200_OK)

        print(f"❌ Authentication failed for: {phone}")
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)


# ✅ Alternative login without custom backend (for testing)
class LoginSellerDirect(APIView):
    """Direct login without custom backend"""
    def post(self, request):
        phone = request.data.get('phone')
        password = request.data.get('password')

        print(f"🔍 Direct login attempt for phone: {phone}")

        if not phone or not password:
            return Response({"error": "Phone and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            seller = Seller.objects.get(phone=phone)
            
            if seller.check_password(password) and seller.is_active:
                # ✅ Create or get token for the seller
                token, created = Token.objects.get_or_create(user=seller)
                
                print(f"✅ Direct login successful for: {phone}")
                return Response({
                    "message": "Login successful",
                    "token": token.key,
                    "shop_url": f"/shop/{seller.phone}"
                }, status=status.HTTP_200_OK)
            else:
                print(f"❌ Password check failed for: {phone}")
                
        except Seller.DoesNotExist:
            print(f"❌ Seller not found for phone: {phone}")
        
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def seller_dashboard(request):
    user = request.user
    print(f"🔍 Dashboard access attempt by: {user}")

    # ✅ Ensure the authenticated user is actually a Seller instance
    if not isinstance(user, Seller):
        print(f"❌ User is not a Seller instance: {type(user)}")
        return Response({"detail": "Invalid user type"}, status=status.HTTP_403_FORBIDDEN)

    serializer = SellerSerializer(user)
    return Response({
        "message": "Seller Dashboard Data",
        "seller": serializer.data,
    }, status=status.HTTP_200_OK)


# ✅ Debug endpoint to check if seller exists
@api_view(['GET'])
def check_seller_exists(request, phone):
    """Debug endpoint to check if seller exists"""
    try:
        seller = Seller.objects.get(phone=phone)
        return Response({
            "exists": True,
            "phone": seller.phone,
            "name": seller.name,
            "shop_name": seller.shop_name,
            "is_active": seller.is_active,
            "created_at": seller.created_at,
        })
    except Seller.DoesNotExist:
        return Response({
            "exists": False,
            "message": f"No seller found with phone: {phone}"
        })


# ✅ Debug endpoint to list all sellers
@api_view(['GET'])
def list_all_sellers(request):
    """Debug endpoint to list all sellers"""
    sellers = Seller.objects.all()
    return Response({
        "count": sellers.count(),
        "sellers": [
            {
                "phone": s.phone,
                "name": s.name,
                "shop_name": s.shop_name,
                "is_active": s.is_active,
            }
            for s in sellers
        ]
    })