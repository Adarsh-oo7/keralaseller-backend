# In store/models.py

from django.db import models
from users.models import Seller  # Import the Seller model from your users app
from django.db.models import Avg        

class StoreProfile(models.Model):
    # --- Existing Fields ---
    seller = models.OneToOneField(Seller, on_delete=models.CASCADE, related_name='store_profile')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    banner_image = models.ImageField(upload_to='store_banners/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    delivery_time_local = models.CharField(
        max_length=50, 
        blank=True, 
        null=True, 
        help_text="Estimated delivery time for local orders (e.g., '2-3 days')"
    )
    delivery_time_national = models.CharField(
        max_length=50, 
        blank=True, 
        null=True, 
        help_text="Estimated delivery time for out-of-state orders (e.g., '5-7 days')"
    )
    # --- START: New Payment Fields ---
    meta_title = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        help_text="SEO title for the shop page (max 100 chars)."
    )
    meta_description = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        help_text="SEO description for the shop page (max 255 chars)."
    )
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
    logo = models.ImageField(upload_to='store_logos/', blank=True, null=True)

    tagline = models.CharField(max_length=150, blank=True, null=True, help_text="A short, catchy slogan for your store.")
    whatsapp_number = models.CharField(max_length=20, blank=True, null=True, help_text="Your business WhatsApp number for customer contact.")
    instagram_link = models.URLField(max_length=200, blank=True, null=True)
    facebook_link = models.URLField(max_length=200, blank=True, null=True)
    def __str__(self):
        return f"Store for {self.seller.name}"
    


# In store/models.py
from django.db import models
from django.db.models import Q, F, CheckConstraint
from django.db import models
from django.db.models import Q, F, CheckConstraint

class Product(models.Model):
    # ✅ Add this nested class for choices
    class SaleType(models.TextChoices):
        ONLINE_AND_OFFLINE = 'BOTH', 'Online & In-Store'
        OFFLINE_ONLY = 'OFFLINE', 'In-Store Only'
        ONLINE_ONLY = 'ONLINE', 'Online Only'

    store = models.ForeignKey('StoreProfile', on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=255)
    model_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Variation of the product (e.g., Red XL, 250g)"
    )
    description = models.TextField(blank=True, null=True) # ✅ Removed duplicate
    price = models.DecimalField(max_digits=10, decimal_places=2)
    mrp = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Maximum Retail Price (defaults to price if blank)"
    )
    total_stock = models.PositiveIntegerField(
        default=0,
        help_text="Total physical stock available (both offline and online)."
    )
    online_stock = models.PositiveIntegerField(
        default=0,
        help_text="Stock allocated for the online store."
    )
    # ✅ Added the missing sale_type field
    sale_type = models.CharField(
        max_length=10,
        choices=SaleType.choices,
        default=SaleType.ONLINE_AND_OFFLINE
    )
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    is_active = models.BooleanField(default=True, help_text="Is the product available for sale?")
    created_at = models.DateTimeField(auto_now_add=True)
    @property
    def average_rating(self):
        return self.reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    class Meta:
        constraints = [
            CheckConstraint(
                check=Q(online_stock__lte=F('total_stock')),
                name='online_stock_lte_total_stock'
            )
        ]
    
    def save(self, *args, **kwargs):
        if self.mrp is None:
            self.mrp = self.price
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

from django.conf import settings # Import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class StockHistory(models.Model):
    class Action(models.TextChoices):
        CREATED = 'CREATED', 'Product Created'
        UPDATED = 'UPDATED', 'Manual Update'
        SALE = 'SALE', 'Sale'
        RETURN = 'RETURN', 'Return'

    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='history')
    
    # ✅ START: Corrected User Fields using GenericForeignKey
    # This allows the 'user' to be either a Seller or a Buyer
    user_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    user_object_id = models.PositiveIntegerField()
    user = GenericForeignKey('user_content_type', 'user_object_id')
    # ✅ END: Corrected User Fields
    
    action = models.CharField(max_length=20, choices=Action.choices)
    change_total = models.IntegerField()
    change_online = models.IntegerField()
    note = models.CharField(max_length=255, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} stock change at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


# In store/models.py
from django.db import models
from django.conf import settings
from users.models import Buyer # Import Buyer

class Review(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='reviews')
    buyer = models.ForeignKey(Buyer, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField(choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4' ), (5, '5')])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Ensure a buyer can only review a product once
        unique_together = ('product', 'buyer')

    def __str__(self):
        return f"{self.rating}-star review for {self.product.name} by {self.buyer.email}"