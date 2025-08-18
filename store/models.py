from django.db import models
from django.db.models import Avg, Q, F, CheckConstraint
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from users.models import Seller, Buyer
from categories.models import Category

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
class Product(models.Model):
    class SaleType(models.TextChoices):
        ONLINE_AND_OFFLINE = 'BOTH', 'Online & In-Store'
        OFFLINE_ONLY = 'OFFLINE', 'In-Store Only'
        ONLINE_ONLY = 'ONLINE', 'Online Only'

    store = models.ForeignKey(StoreProfile, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    name = models.CharField(max_length=255)
    model_name = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    mrp = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_stock = models.PositiveIntegerField(default=0)
    online_stock = models.PositiveIntegerField(default=0)
    sale_type = models.CharField(max_length=10, choices=SaleType.choices, default=SaleType.ONLINE_AND_OFFLINE)
    main_image = models.ImageField(upload_to='product_images/main/', blank=True, null=True)
    attributes = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # image = models.ImageField(upload_to='products/', blank=True, null=True)

    @property
    def average_rating(self):
        return self.reviews.aggregate(Avg('rating'))['rating__avg'] or 0

    class Meta:
        constraints = [CheckConstraint(check=Q(online_stock__lte=F('total_stock')), name='online_stock_lte_total_stock')]
    
    def save(self, *args, **kwargs):
        if self.mrp is None: self.mrp = self.price
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='sub_images')
    image = models.ImageField(upload_to='product_images/sub/')

    def __str__(self):
        return f"Image for {self.product.name}"

# ==============================================================================
# REVIEW & HISTORY MODELS
# ==============================================================================
class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    buyer = models.ForeignKey(Buyer, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('product', 'buyer')

class StockHistory(models.Model):
    class Action(models.TextChoices):
        CREATED = 'CREATED', 'Product Created'
        UPDATED = 'UPDATED', 'Manual Update'
        SALE = 'SALE', 'Sale'
        RETURN = 'RETURN', 'Return'

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='history')
    user_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    user_object_id = models.PositiveIntegerField()
    user = GenericForeignKey('user_content_type', 'user_object_id')
    action = models.CharField(max_length=20, choices=Action.choices)
    change_total = models.IntegerField()
    change_online = models.IntegerField()
    note = models.CharField(max_length=255, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)