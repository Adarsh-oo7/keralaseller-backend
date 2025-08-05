from rest_framework import serializers
from .models import StoreProfile, Product

class ProductSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'model_name', 'description', 
            'price', 'mrp', 'total_stock', 'online_stock', 
            'sale_type',  # ✅ This field was missing
            'image_url', 'is_active', 'image'
        ]
        read_only_fields = ['id', 'image_url']
        extra_kwargs = {
            'image': {'write_only': True, 'required': False}
        }
        
    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            return request.build_absolute_uri(obj.image.url)
        return None
    

class StoreProfileSerializer(serializers.ModelSerializer):
    banner_image_url = serializers.SerializerMethodField()
    logo_url = serializers.SerializerMethodField()
    seller_phone = serializers.CharField(source='seller.phone', read_only=True)

    class Meta:
        model = StoreProfile
        fields = [
            'name', 'description', 
            'banner_image', 'banner_image_url', 
            'logo', 'logo_url',
            'seller_phone', # ✅ Add the new field to the list

            'payment_method', 'razorpay_key_id', 'razorpay_key_secret',
            'upi_id', 'accepts_cod',
            'tagline', 'whatsapp_number', 'instagram_link', 'facebook_link'
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
    

from .models import StockHistory

class StockHistorySerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField() # Show user's string representation
    product = serializers.StringRelatedField() # Show product name

    class Meta:
        model = StockHistory
        fields = ['id', 'product', 'user', 'action', 'change_total', 'change_online', 'note', 'timestamp']
