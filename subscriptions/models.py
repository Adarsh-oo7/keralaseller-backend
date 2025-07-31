from django.db import models
from django.conf import settings
from django.utils import timezone
import datetime

class Plan(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    product_limit = models.PositiveIntegerField()
    duration_days = models.PositiveIntegerField(help_text="Duration of the plan in days (e.g., 30 for monthly)")

    def __str__(self):
        return self.name

class Subscription(models.Model):
    seller = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True, blank=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=200, blank=True, null=True)

    def is_active(self):
        if self.end_date:
            return self.end_date > timezone.now()
        return False
    
    def __str__(self):
        return f"{self.seller.name}'s Subscription"