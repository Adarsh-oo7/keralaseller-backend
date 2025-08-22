from django.db import models
from django.db.models import Avg, Q, F, CheckConstraint
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from users.models import Seller, Buyer

# ==============================================================================
# STORE PROFILE MODEL
# ==============================================================================
class StoreProfile(models.Model):
    seller = models.OneToOneField(Seller, on_delete=models.CASCADE, related_name='store_profile')
    name = models.CharField(max_length=200)
    tagline = models.CharField(max_length=150, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='store_logos/', blank=True, null=True)
    banner_image = models.ImageField(upload_to='store_banners/', blank=True, null=True)
    whatsapp_number = models.CharField(max_length=20, blank=True, null=True)
    instagram_link = models.URLField(max_length=200, blank=True, null=True)
    facebook_link = models.URLField(max_length=200, blank=True, null=True)
    delivery_time_local = models.CharField(max_length=50, blank=True, null=True)
    delivery_time_national = models.CharField(max_length=50, blank=True, null=True)
    meta_title = models.CharField(max_length=100, blank=True, null=True)
    meta_description = models.CharField(max_length=255, blank=True, null=True)
    
    PAYMENT_CHOICES = [('RAZORPAY', 'Razorpay'), ('UPI', 'UPI Link'), ('NONE', 'None')]
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default='NONE')
    razorpay_key_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_key_secret = models.CharField(max_length=100, blank=True, null=True)
    upi_id = models.CharField(max_length=100, blank=True, null=True)
    accepts_cod = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# ==============================================================================
# PRODUCT MODELS
# ==============================================================================
