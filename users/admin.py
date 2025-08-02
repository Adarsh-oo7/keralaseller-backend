from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Seller, SellerManager, Buyer, BuyerManager

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
    
    # ✅ This line tells the admin to display these fields as non-editable text
    readonly_fields = ('last_login', 'created_at', 'updated_at')
    
    # Required for custom user admin
    ordering = ('phone',)

# Register your models with the admin site
admin.site.register(Seller, SellerAdmin)
admin.site.register(Buyer)                           
# Register the custom user admin for Buyer  