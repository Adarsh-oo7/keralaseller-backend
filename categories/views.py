from django.shortcuts import render

# Create your views here.
from rest_framework import generics, permissions
from .models import Category
from .serializers import CategorySerializer

class CategoryListView(generics.ListAPIView):
    """
    Provides a list of all product categories and their specific attributes.
    """
    queryset = Category.objects.prefetch_related('attributes').all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated] # For sellers in the dashboard