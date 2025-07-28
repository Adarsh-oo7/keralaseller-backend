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
    
class StoreProfileSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True) # Nest products in store profile

    class Meta:
        model = StoreProfile
        fields = ['name', 'description', 'banner_image', 'products']