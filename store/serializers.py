import json
from rest_framework import serializers
from .models import Product, StoreProfile, StockHistory, Review
from users.models import Buyer

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

# ==============================================================================
# MAIN SERIALIZERS
# ==============================================================================

class ProductSerializer(serializers.ModelSerializer):
    # ✅ Fixed: Use main_image_url and keep image_url for compatibility
    main_image_url = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    sub_images = serializers.SerializerMethodField()
    store = NestedStoreProfileSerializer(read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    review_count = serializers.IntegerField(source='reviews.count', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'model_name', 'description', 'price', 'mrp', 
            'total_stock', 'online_stock', 'sale_type', 'main_image_url', 
            'image_url', 'sub_images', 'is_active', 'store', 'category', 
            'attributes', 'average_rating', 'review_count', 'main_image'
        ]
        read_only_fields = ['id', 'main_image_url', 'image_url', 'sub_images', 'store', 'average_rating', 'review_count']
        extra_kwargs = {
            'main_image': {'write_only': True, 'required': False},
            'attributes': {'required': False},
        }
        
    def get_main_image_url(self, obj):
        """Return the full URL for the main image"""
        request = self.context.get('request')
        if obj.main_image and hasattr(obj.main_image, 'url'):
            if request:
                return request.build_absolute_uri(obj.main_image.url)
            return obj.main_image.url
        return None

    def get_image_url(self, obj):
        """Return main_image_url for backward compatibility"""
        # ✅ This ensures your frontend gets the image_url it's looking for
        return self.get_main_image_url(obj)
    
    def get_sub_images(self, obj):
        """Return list of sub-image URLs"""
        request = self.context.get('request')
        sub_images = []
        
        # Get related sub images
        for sub_image in obj.sub_images.all():
            if sub_image.image:
                if request:
                    url = request.build_absolute_uri(sub_image.image.url)
                else:
                    url = sub_image.image.url
                sub_images.append({
                    'id': sub_image.id,
                    'image_url': url
                })
        return sub_images

    def validate_attributes(self, value):
        """Validate and parse attributes field."""
        if value is None:
            return {}
        
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                raise serializers.ValidationError("Invalid JSON format for attributes.")
        
        if isinstance(value, dict):
            return value
        
        return {}

    def validate_online_stock(self, value):
        """Ensure online stock is not negative."""
        if value < 0:
            raise serializers.ValidationError("Online stock cannot be negative.")
        return value

    def validate_total_stock(self, value):
        """Ensure total stock is not negative."""
        if value < 0:
            raise serializers.ValidationError("Total stock cannot be negative.")
        return value

    def validate(self, attrs):
        """Cross-field validation."""
        online_stock = attrs.get('online_stock', 0)
        total_stock = attrs.get('total_stock', 0)
        
        # For updates, get current values if not provided
        if self.instance:
            online_stock = attrs.get('online_stock', self.instance.online_stock)
            total_stock = attrs.get('total_stock', self.instance.total_stock)
        
        if online_stock > total_stock:
            raise serializers.ValidationError(
                {"online_stock": "Online stock cannot be greater than total stock."}
            )
        
        return attrs

    def create(self, validated_data):
        """Handle creation with proper attribute parsing."""
        # Handle attributes
        attributes_data = validated_data.pop('attributes', {})
        if isinstance(attributes_data, str):
            try:
                validated_data['attributes'] = json.loads(attributes_data)
            except json.JSONDecodeError:
                validated_data['attributes'] = {}
        else:
            validated_data['attributes'] = attributes_data or {}

        # Create the product instance
        product = super().create(validated_data)
        return product

    def update(self, instance, validated_data):
        """Handle updates for category and dynamic JSON attributes."""
        # Handle category
        category_id = validated_data.pop('category', None)
        if category_id:
            instance.category_id = category_id

        # Handle attributes
        attributes_data = validated_data.pop('attributes', None)
        if attributes_data is not None:
            if isinstance(attributes_data, str):
                try:
                    instance.attributes = json.loads(attributes_data)
                except json.JSONDecodeError:
                    instance.attributes = {}
            else:
                instance.attributes = attributes_data
        
        return super().update(instance, validated_data)

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

class StockHistorySerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    product = serializers.StringRelatedField()

    class Meta:
        model = StockHistory
        fields = ['id', 'product', 'user', 'action', 'change_total', 'change_online', 'note', 'timestamp']

class ReviewSerializer(serializers.ModelSerializer):
    buyer = SimpleBuyerSerializer(read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'buyer', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'buyer', 'created_at']