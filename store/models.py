# In store/models.py

from django.db import models
from users.models import Seller  # Import the Seller model from your users app


class StoreProfile(models.Model):
    # --- Existing Fields ---
    seller = models.OneToOneField(Seller, on_delete=models.CASCADE, related_name='store_profile')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    banner_image = models.ImageField(upload_to='store_banners/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # --- START: New Payment Fields ---
    PAYMENT_CHOICES = [
        ('RAZORPAY', 'Razorpay'),
        ('UPI', 'UPI Link'),
        ('NONE', 'None'),
    ]
    payment_method = models.CharField(
        max_length=10,
        choices=PAYMENT_CHOICES,
        default='NONE'
    )
    razorpay_key_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_key_secret = models.CharField(max_length=100, blank=True, null=True)
    upi_id = models.CharField(max_length=100, blank=True, null=True)
    accepts_cod = models.BooleanField(default=False, help_text="Accept Cash on Delivery")
    # --- END: New Payment Fields ---

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