from rest_framework import serializers
from .models import Product, StoreProfile, StockHistory

# A simplified serializer for nesting store info inside a product
class NestedStoreProfileSerializer(serializers.ModelSerializer):
    seller_phone = serializers.CharField(source='seller.phone', read_only=True)
    class Meta:
        model = StoreProfile
        fields = ['name', 'seller_phone']

class ProductSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    # ✅ Nest the store details to make seller_phone available on the shop page
    store = NestedStoreProfileSerializer(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'model_name', 'description', 'price', 'mrp', 
            'total_stock', 'online_stock', 'sale_type', 'image_url', 
            'is_active', 'image', 'store'
        ]
        read_only_fields = ['id', 'image_url', 'store']
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
        # ... (method is correct)
        pass

    def get_logo_url(self, obj):
        # ... (method is correct)
        pass

class StockHistorySerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    product = serializers.StringRelatedField()

    class Meta:
        model = StockHistory
        fields = ['id', 'product', 'user', 'action', 'change_total', 'change_online', 'note', 'timestamp']