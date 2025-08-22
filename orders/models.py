from django.db import models
from django.utils import timezone
from store.models import StoreProfile
from users.models import Buyer
from products.models import Product

class Order(models.Model):
    class OrderStatus(models.TextChoices):
        # ✅ New and updated statuses for the escrow workflow
        PENDING_PAYMENT = 'PENDING_PAYMENT', 'Pending Payment'
        HELD_FOR_SELLER_ACCEPTANCE = 'HELD', 'Payment Held for Acceptance'
        ACCEPTED_BY_SELLER = 'ACCEPTED', 'Accepted by Seller'
        SHIPPED = 'SHIPPED', 'Shipped'
        DELIVERED = 'DELIVERED', 'Delivered'
        CANCELLED = 'CANCELLED', 'Cancelled'
        REFUNDED = 'REFUNDED', 'Refunded'

    store = models.ForeignKey(StoreProfile, on_delete=models.CASCADE, related_name='orders')
    buyer = models.ForeignKey(Buyer, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    customer_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=20)
    shipping_address = models.TextField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING_PAYMENT
    )
    shipping_provider = models.CharField(max_length=100, blank=True, null=True)
    tracking_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # ✅ New timestamp fields to track deadlines
    paid_at = models.DateTimeField(null=True, blank=True)
    seller_accepted_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Order #{self.id} for {self.store.name}"

class OrderItem(models.Model):
    # This model is correct and does not need changes
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price at the time of purchase")

    def __str__(self):
        return f"{self.quantity} x {self.product.name if self.product else 'Deleted Product'}"