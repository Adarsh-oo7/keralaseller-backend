from rest_framework import serializers
from django.core.cache import cache
from .models import Seller, Buyer


class SellerSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying seller dashboard information.
    """
    class Meta:
        model = Seller
        fields = ['phone', 'name', 'shop_name', 'email', 'address', 'created_at', 'is_active']
        read_only_fields = ['phone', 'created_at']


class RegisterSellerSerializer(serializers.ModelSerializer):
    """
    Serializer for handling new seller registration with OTP validation.
    """
    otp = serializers.CharField(write_only=True, required=True)
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = Seller
        fields = ['phone', 'password', 'name', 'shop_name', 'email', 'address', 'otp']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def validate_phone(self, value):
        """Validate phone number format"""
        import re
        if not re.match(r'^\d{10}$', str(value)):
            raise serializers.ValidationError("Please enter a valid 10-digit phone number.")
        return value

    def validate_email(self, value):
        """Validate email uniqueness"""
        if value and Seller.objects.filter(email=value).exists():
            raise serializers.ValidationError("A seller with this email already exists.")
        return value

    def validate(self, data):
        phone = data.get('phone')
        otp = data.get('otp')

        # Check for existing user by phone
        if Seller.objects.filter(phone=phone).exists():
            raise serializers.ValidationError("A seller with this phone number already exists.")

        # Check OTP from cache
        stored_otp = cache.get(f"otp_{phone}")
        if not stored_otp or str(stored_otp) != str(otp):
            raise serializers.ValidationError("The OTP provided is invalid or has expired.")

        return data

    def create(self, validated_data):
        # Remove otp from data before creating the user object
        otp_value = validated_data.pop('otp')
        phone = validated_data.get('phone')
        
        # Extract password and hash it properly
        password = validated_data.pop('password')
        
        # Create seller instance
        seller = Seller.objects.create(**validated_data)
        
        # Set password (this will hash it)
        seller.set_password(password)
        seller.save()
        
        # Clear the OTP from cache after successful registration
        cache.delete(f"otp_{phone}")
        
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
        """Validate phone number format if provided"""
        if value:
            import re
            if not re.match(r'^\d{10}$', str(value)):
                raise serializers.ValidationError("Please enter a valid 10-digit phone number.")
        return value

    def validate_pincode(self, value):
        """Validate pincode format if provided"""
        if value:
            import re
            if not re.match(r'^\d{6}$', str(value)):
                raise serializers.ValidationError("Please enter a valid 6-digit pincode.")
        return value
