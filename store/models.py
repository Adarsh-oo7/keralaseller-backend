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

class Product(models.Model):
    store = models.ForeignKey('StoreProfile', on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    mrp = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Maximum Retail Price (defaults to price if blank)"
    )
    model_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Variation of the product (e.g., Red XL, 250g)"
    )
    total_stock = models.PositiveIntegerField(
        default=0,
        help_text="Total physical stock available (both offline and online)."
    )
    online_stock = models.PositiveIntegerField(
        default=0,
        help_text="Stock allocated for the online store."
    )
    description = models.TextField(blank=True, null=True)

    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    is_active = models.BooleanField(default=True, help_text="Is the product visible in the online store?")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            CheckConstraint(
                check=Q(online_stock__lte=F('total_stock')),
                name='online_stock_lte_total_stock'
            )
        ]
    
    def save(self, *args, **kwargs):
        # If MRP is not provided, set it to the selling price automatically
        if self.mrp is None:
            self.mrp = self.price
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    

from django.conf import settings # Import settings

class StockHistory(models.Model):
    class Action(models.TextChoices):
        CREATED = 'CREATED', 'Product Created'
        UPDATED = 'UPDATED', 'Manual Update'
        SALE = 'SALE', 'Sale'
        RETURN = 'RETURN', 'Return'

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='history')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    note = models.CharField(max_length=255, blank=True, null=True, help_text="Reason for the stock change")

    action = models.CharField(max_length=20, choices=Action.choices)
    change_total = models.IntegerField(help_text="Change in total stock (e.g., +10 or -2)")
    change_online = models.IntegerField(help_text="Change in online stock (e.g., +5 or -1)")
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} stock change at {self.timestamp}"
