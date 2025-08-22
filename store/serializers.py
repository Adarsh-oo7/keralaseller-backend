from rest_framework import serializers
from .models import StoreProfile  # Only import StoreProfile from store.models

class StoreProfileSerializer(serializers.ModelSerializer):
    banner_image_url = serializers.SerializerMethodField()
    logo_url = serializers.SerializerMethodField()
    seller_phone = serializers.CharField(source='seller.phone', read_only=True)

    class Meta:
        model = StoreProfile
        fields = [
            'name', 'description', 'banner_image', 'banner_image_url', 
            'logo', 'logo_url', 'seller_phone', 'payment_method', 
            'razorpay_key_id', 'razorpay_key_secret', 'upi_id', 'accepts_cod',
            'tagline', 'whatsapp_number', 'instagram_link', 'facebook_link',
            'delivery_time_local', 'delivery_time_national',
            'meta_title', 'meta_description'
        ]
        extra_kwargs = {
            'banner_image': {'write_only': True, 'required': False},
            'logo': {'write_only': True, 'required': False},
            'razorpay_key_secret': {'write_only': True, 'required': False}
        }
    
    def get_banner_image_url(self, obj):
        request = self.context.get('request')
        if obj.banner_image and hasattr(obj.banner_image, 'url'):
            return request.build_absolute_uri(obj.banner_image.url)
        return None

    def get_logo_url(self, obj):
        request = self.context.get('request')
        if obj.logo and hasattr(obj.logo, 'url'):
            return request.build_absolute_uri(obj.logo.url)
        return None
