from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Seller, Buyer

@admin.register(Seller)
class SellerAdmin(UserAdmin):
    # The fields to display in the list view of the admin
    list_display = ('phone', 'name', 'shop_name', 'is_active', 'is_staff')
    # The fields to use for searching
    search_fields = ('phone', 'name', 'shop_name')
    # The fields to use for filtering
    list_filter = ('is_active', 'is_staff')
    
    # This defines the layout of the form when you edit a seller
    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        ('Personal Info', {'fields': ('name', 'email', 'shop_name', 'address')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    
    readonly_fields = ('last_login', 'created_at', 'updated_at')
    ordering = ('phone',)
    # This is needed because the default UserAdmin requires it
    filter_horizontal = ()

@admin.register(Buyer)
class BuyerAdmin(UserAdmin):
    """
    Admin configuration for the Buyer model.
    """
    list_display = ('email', 'full_name', 'is_staff', 'is_active')
    search_fields = ('email', 'full_name')
    list_filter = ('is_staff', 'is_active')
    ordering = ('email',)
    
    # Use 'email' as the username field in the admin
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('full_name', 'phone_number', 'phone_verified')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {'fields': ('email', 'password')}),
    )
    readonly_fields = ('last_login',)
    
    filter_horizontal = ()