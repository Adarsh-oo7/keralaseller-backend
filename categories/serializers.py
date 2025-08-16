from rest_framework import serializers
from .models import Category, Attribute

class AttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attribute
        fields = ['id', 'name']
# In categories/serializers.py
class CategorySerializer(serializers.ModelSerializer):
    attributes = AttributeSerializer(many=True, read_only=True)
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'attributes', 'default_attributes'] # ✅ Add the new field