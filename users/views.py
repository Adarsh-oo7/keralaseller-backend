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
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def seller_dashboard(request):
    """
    Provides dashboard data for the authenticated seller.
    """
    # request.user is the authenticated Seller instance
    serializer = SellerSerializer(request.user)
    return Response({
        "message": "Seller Dashboard Data",
        "seller": serializer.data,
    }, status=status.HTTP_200_OK)