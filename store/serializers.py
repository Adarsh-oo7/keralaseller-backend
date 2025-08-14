from rest_framework import serializers
from .models import Product, StoreProfile, StockHistory, Review
from users.models import Buyer  # Import Buyer model for reviews
from django.db.models import Avg  # Import Avg for calculating average rating
# A simplified serializer for nesting store info inside a product
class NestedStoreProfileSerializer(serializers.ModelSerializer):
    seller_phone = serializers.CharField(source='seller.phone', read_only=True)
    class Meta:
        model = StoreProfile
        fields = ['name', 'seller_phone']

# A simplified serializer for nesting store info inside a product
class NestedStoreProfileSerializer(serializers.ModelSerializer):
    seller_phone = serializers.CharField(source='seller.phone', read_only=True)
    whatsapp_number = serializers.CharField(read_only=True)
    class Meta:
        model = StoreProfile
        fields = ['name', 'seller_phone', 'whatsapp_number']


class ProductSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    # ✅ Nest the store details to make seller info available on public pages
    store = NestedStoreProfileSerializer(read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    review_count = serializers.IntegerField(source='reviews.count', read_only=True)



    class Meta:
        model = Product
        fields = [
            'id', 'name', 'model_name', 'description', 
            'price', 'mrp', 'total_stock', 'online_stock', 
            'sale_type', 'image_url', 'is_active', 'image',
            'store' , 'average_rating', 'review_count'
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

class SimpleBuyerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Buyer
        fields = ['full_name']


class ReviewSerializer(serializers.ModelSerializer):
    # Use the simple serializer to show the buyer's name
    buyer = SimpleBuyerSerializer(read_only=True)

    class Meta:
        model = Review
        # 'product' and 'buyer' will be set automatically in the view
        fields = ['id', 'buyer', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'buyer', 'created_at']