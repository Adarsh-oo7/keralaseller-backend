# In store/models.py

from django.db import models
from users.models import Seller  # Import the Seller model from your users app

class StoreProfile(models.Model):
    seller = models.OneToOneField(Seller, on_delete=models.CASCADE, related_name='store_profile')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    # You will need to install Pillow for ImageField: pip install Pillow
    banner_image = models.ImageField(upload_to='store_banners/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Store for {self.seller.name}"

class Product(models.Model):
    store = models.ForeignKey(StoreProfile, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='product_images/')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name