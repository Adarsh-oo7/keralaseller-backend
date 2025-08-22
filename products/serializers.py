import json
from rest_framework import serializers
from .models import Product, ProductImage, Review, StockHistory
from store.models import StoreProfile
from users.models import Buyer
from .models import Product, ProductImage

# ==============================================================================
# NESTED & SIMPLE SERIALIZERS
# ==============================================================================

class NestedStoreProfileSerializer(serializers.ModelSerializer):
    """A simplified serializer for nesting store info inside a product."""
    seller_phone = serializers.CharField(source='seller.phone', read_only=True)
    whatsapp_number = serializers.CharField(read_only=True)
    class Meta:
        model = StoreProfile
        fields = ['name', 'seller_phone', 'whatsapp_number']

class SimpleBuyerSerializer(serializers.ModelSerializer):
    """A simple serializer to show the buyer's name in reviews."""
    class Meta:
        model = Buyer
        fields = ['full_name']

class ProductImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'image_url']
    
    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            if request:
                return request.build_absolute_uri(obj.image.url)
        return None

# ==============================================================================
# MAIN SERIALIZERS
# ==============================================================================

class ProductSerializer(serializers.ModelSerializer):
    main_image_url = serializers.SerializerMethodField()
    sub_images = ProductImageSerializer(many=True, read_only=True)
    store = NestedStoreProfileSerializer(read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    review_count = serializers.IntegerField(source='reviews.count', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'model_name', 'description', 'price', 'mrp', 
            'total_stock', 'online_stock', 'sale_type', 'main_image', 'main_image_url', 
            'sub_images', 'is_active', 'store', 'category', 'attributes', 
            'average_rating', 'review_count'
        ]
        read_only_fields = ['id', 'main_image_url', 'sub_images', 'store', 'average_rating', 'review_count']
        extra_kwargs = {
            'main_image': {'write_only': True, 'required': False},
            'attributes': {'required': False},
        }

    def get_main_image_url(self, obj):
        request = self.context.get('request')
        if obj.main_image and hasattr(obj.main_image, 'url'):
            if request:
                return request.build_absolute_uri(obj.main_image.url)
        return None
    
    # Pass context to nested serializers
    def get_sub_images(self, obj):
        sub_images = obj.sub_images.all()
        return ProductImageSerializer(sub_images, many=True, context=self.context).data
        
    def validate(self, attrs):
        online_stock = attrs.get('online_stock', self.instance.online_stock if self.instance else 0)
        total_stock = attrs.get('total_stock', self.instance.total_stock if self.instance else 0)
        if online_stock > total_stock:
            raise serializers.ValidationError({"online_stock": "Online stock cannot be greater than total stock."})
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        attributes_data = validated_data.pop('attributes', {})
        if isinstance(attributes_data, str):
            validated_data['attributes'] = json.loads(attributes_data)
        
        instance = super().create(validated_data)
        instance._current_user = user
        return instance

    def update(self, instance, validated_data):
        attributes_data = validated_data.pop('attributes', None)
        if attributes_data is not None:
            if isinstance(attributes_data, str):
                instance.attributes = json.loads(attributes_data)
            else:
                instance.attributes = attributes_data
        return super().update(instance, validated_data)

class ReviewSerializer(serializers.ModelSerializer):
    buyer = SimpleBuyerSerializer(read_only=True)
    class Meta:
        model = Review
        fields = ['id', 'buyer', 'rating', 'comment', 'created_at']

class StockHistorySerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    product = serializers.StringRelatedField()
    class Meta:
        model = StockHistory
        fields = ['id', 'product', 'user', 'action', 'change_total', 'change_online', 'note', 'timestamp']