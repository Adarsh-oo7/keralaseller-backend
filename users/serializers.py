from rest_framework import serializers
from .models import Seller

class SellerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seller
        fields = ['id', 'phone', 'name', 'shop_name', 'email', 'address', 'created_at', 'is_active']
        read_only_fields = ['id', 'created_at']