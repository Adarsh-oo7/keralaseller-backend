from rest_framework import serializers
from .models import Plan, Subscription

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ['id', 'name', 'price', 'product_limit', 'duration_days']

class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)
    is_active = serializers.BooleanField(source='is_active', read_only=True)

    class Meta:
        model = Subscription
        fields = ['plan', 'start_date', 'end_date', 'is_active']