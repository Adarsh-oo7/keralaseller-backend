from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

# ✅ Custom Manager
class SellerManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError("The phone number is required")

        extra_fields.setdefault("is_active", True)
        seller = self.model(phone=phone, **extra_fields)
        seller.set_password(password)
        seller.save(using=self._db)
        return seller

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(phone, password, **extra_fields)


# ✅ Custom User Model (Seller)
class Seller(AbstractBaseUser, PermissionsMixin):
    phone = models.CharField(max_length=15, unique=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    shop_name = models.CharField(max_length=150, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)


    # Required for authentication
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)  # Provided by PermissionsMixin but kept for clarity

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = SellerManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []  # No extra required fields when creating superuser

    def __str__(self):
        return f"{self.phone} - {self.name if self.name else 'Seller'}"



from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db.models.signals import post_save
from django.dispatch import receiver
from store.models import StoreProfile

# ✅ CORRECTED SIGNAL with fallback logic
@receiver(post_save, sender=Seller)
def create_store_profile_for_seller(sender, instance, created, **kwargs):
    """
    Automatically create a StoreProfile when a new Seller is created.
    """
    if created:
        # Use shop_name if it exists, otherwise create a default name
        store_name = instance.shop_name or f"{instance.name}'s Store"
        
        # An absolute fallback in case both name and shop_name are empty
        if not store_name.strip():
            store_name = f"Store for {instance.phone}"

        StoreProfile.objects.create(seller=instance, name=store_name)
        print(f"StoreProfile created for seller: {instance.name} with name '{store_name}'")