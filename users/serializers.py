# In users/serializers.py

from rest_framework import serializers
from django.core.cache import cache
from .models import Seller, Buyer

class SellerSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying seller dashboard information.
    """
    class Meta:
        model = Seller
        fields = ['phone', 'name', 'shop_name', 'email', 'address', 'created_at']


class RegisterSellerSerializer(serializers.ModelSerializer):
    """
    Serializer for handling new seller registration with OTP validation.
    """
    otp = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = Seller
        # List all fields coming from the frontend registration form
        fields = ['phone', 'password', 'name', 'shop_name', 'email', 'otp']
        extra_kwargs = {
            'password': {'write_only': True}, # Ensure password is not sent back in response
        }

    def validate(self, data):
        phone = data.get('phone')
        otp = data.get('otp')

        # Check for existing user
        if Seller.objects.filter(phone=phone).exists():
            raise serializers.ValidationError("A seller with this phone number already exists.")

        # Check OTP from cache
        stored_otp = cache.get(f"otp_{phone}")
        if not stored_otp or str(stored_otp) != otp:
            raise serializers.ValidationError("The OTP provided is invalid or has expired.")

        return data

    def create(self, validated_data):
        # Remove otp from data before creating the user object
        validated_data.pop('otp')
        # Use the custom manager's create_user method to ensure password is hashed
        user = Seller.objects.create_user(**validated_data)
        return user
    
class BuyerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Buyer
        fields = ['id', 'email', 'full_name', 'phone_number', 'phone_verified']
