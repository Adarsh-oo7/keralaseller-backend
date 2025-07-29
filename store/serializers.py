# In store/serializers.py

from rest_framework import serializers
from .models import StoreProfile, Product

# In store/serializers.py
from rest_framework import serializers
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
    # This new field will contain the full URL to the image
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        # Use image_url in the fields list instead of 'image'
        fields = ['id', 'name', 'description', 'price', 'stock', 'image_url', 'is_active']
        read_only_fields = ['id', 'image_url']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            return request.build_absolute_uri(obj.image.url)
        return None
    
# In store/serializers.py
# In store/serializers.py
class StoreProfileSerializer(serializers.ModelSerializer):
    banner_image_url = serializers.SerializerMethodField()
    # Add a new method field for the logo URL
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = StoreProfile
        fields = [
            'name', 'description', 
            'banner_image', 'banner_image_url', 
            'logo', 'logo_url', # Add the new logo fields
            'payment_method', 'razorpay_key_id', 'razorpay_key_secret',
            'upi_id', 'accepts_cod',
            'tagline', 'whatsapp_number', 'instagram_link', 'facebook_link'
        ]
        extra_kwargs = {
            'banner_image': {'write_only': True, 'required': False},
            'logo': {'write_only': True, 'required': False}, # Make logo write-only
            'razorpay_key_secret': {'write_only': True, 'required': False}
        }

    def get_banner_image_url(self, obj):
        request = self.context.get('request')
        if obj.banner_image and hasattr(obj.banner_image, 'url'):
            return request.build_absolute_uri(obj.banner_image.url)
        return None

    # Add a new method to get the full logo URL
    def get_logo_url(self, obj):
        request = self.context.get('request')
        if obj.logo and hasattr(obj.logo, 'url'):
            return request.build_absolute_uri(obj.logo.url)
        return None