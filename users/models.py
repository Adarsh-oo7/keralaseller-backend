from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

# ==============================================================================
# SELLER MODEL AND MANAGER
# ==============================================================================

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
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(phone, password, **extra_fields)

class Seller(AbstractBaseUser, PermissionsMixin):
    phone = models.CharField(max_length=15, unique=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    shop_name = models.CharField(max_length=150, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Fix for clashing reverse accessors with Buyer model
    groups = models.ManyToManyField('auth.Group', related_name='seller_set', blank=True)
    user_permissions = models.ManyToManyField('auth.Permission', related_name='seller_permissions_set', blank=True)

    objects = SellerManager()
    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{self.phone} - {self.name if self.name else 'Seller'}"

# ==============================================================================
# BUYER MODEL AND MANAGER
# ==============================================================================

class BuyerManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class Buyer(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)


    phone_number = models.CharField(max_length=15, blank=True, null=True, unique=True)
    phone_verified = models.BooleanField(default=False)

    address_line_1 = models.CharField(max_length=255, blank=True, null=True)
    address_line_2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)

    # Fix for clashing reverse accessors with Seller model
    groups = models.ManyToManyField('auth.Group', related_name='buyer_set', blank=True)
    user_permissions = models.ManyToManyField('auth.Permission', related_name='buyer_permissions_set', blank=True)
    
    objects = BuyerManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email
    

# ✅ Add this new custom token model for sellers
class SellerToken(models.Model):
    key = models.CharField(max_length=40, primary_key=True)
    user = models.OneToOneField(
        Seller, # Directly link to the Seller model
        related_name='auth_token',
        on_delete=models.CASCADE
    )
    created = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super().save(*args, **kwargs)

    @classmethod
    def generate_key(cls):
        import binascii
        import os
        return binascii.hexlify(os.urandom(20)).decode()

    def __str__(self):
        return self.key