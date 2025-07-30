# In orders/serializers.py
from rest_framework import serializers
from .models import Order, OrderItem
from store.serializers import ProductSerializer # We can reuse this for product details

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'price']

class OrderSerializer(serializers.ModelSerializer):
    # Nest the items within the order for detailed view
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'customer_name', 'customer_phone', 'shipping_address', 'total_amount', 'status', 'created_at', 'items']