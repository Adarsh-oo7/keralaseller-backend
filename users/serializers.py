from rest_framework import serializers
from django.core.cache import cache
from .models import Seller, Buyer
import re

class SellerSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying seller dashboard information.
    """
    class Meta:
        model = Seller
        fields = ['id', 'phone', 'name', 'shop_name', 'email', 'address', 'created_at']
        read_only_fields = ['id', 'phone', 'created_at']

class RegisterSellerSerializer(serializers.ModelSerializer):
    """
    Serializer for handling new seller registration with OTP validation.
    """
    otp = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = Seller
        fields = ['phone', 'password', 'name', 'shop_name', 'email', 'address', 'otp']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def validate(self, data):
        phone = data.get('phone')
        otp = data.get('otp')

        if Seller.objects.filter(phone=phone).exists():
            raise serializers.ValidationError("A seller with this phone number already exists.")

        stored_otp = cache.get(f"otp_{phone}")
        if not stored_otp or str(stored_otp) != str(otp):
            raise serializers.ValidationError("The OTP provided is invalid or has expired.")

        return data

    def create(self, validated_data):
        """
        Creates a new seller using the custom manager to ensure
        the password is properly hashed.
        """
        # Remove the OTP from the data before creating the user
        validated_data.pop('otp')
        
        # ✅ Use the create_user method which handles password hashing
        seller = Seller.objects.create_user(**validated_data)
        
        # Clear the OTP from cache
        cache.delete(f"otp_{seller.phone}")
        
        return seller

class BuyerSerializer(serializers.ModelSerializer):
    """
    Serializer for buyer profile management.
    """
    class Meta:
        model = Buyer
        fields = [
            'id', 'email', 'full_name', 'phone_number', 'phone_verified',
            'address_line_1', 'address_line_2', 'city', 'pincode'
        ]
        read_only_fields = ['id', 'email', 'phone_verified']

    def validate_phone_number(self, value):
        if value and not re.match(r'^\d{10}$', str(value)):
            raise serializers.ValidationError("Please enter a valid 10-digit phone number.")
        return value

    def validate_pincode(self, value):
        if value and not re.match(r'^\d{6}$', str(value)):
            raise serializers.ValidationError("Please enter a valid 6-digit pincode.")
        return value