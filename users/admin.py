from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Seller, Buyer
from .forms import SellerCreationForm, SellerChangeForm # ✅ Import the new forms

@admin.register(Seller)
class SellerAdmin(UserAdmin):
    # ✅ Tell the admin to use your custom forms
    form = SellerChangeForm
    add_form = SellerCreationForm

    # The rest of your SellerAdmin is unchanged
    list_display = ('phone', 'name', 'shop_name', 'is_staff', 'is_active')
    search_fields = ('phone', 'name', 'shop_name')
    ordering = ('phone',)
    
    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        ('Personal Info', {'fields': ('name', 'shop_name', 'email', 'address')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'password', 'password2'),
        }),
    )
    
    readonly_fields = ('last_login', 'created_at', 'updated_at')
    filter_horizontal = ()

@admin.register(Buyer)
class BuyerAdmin(UserAdmin):
    list_display = ('email', 'full_name', 'is_staff', 'is_active')
    search_fields = ('email', 'full_name')
    list_filter = ('is_staff', 'is_active')
    ordering = ('email',)
    
    # This is needed to tell UserAdmin to use 'email' instead of 'username'
    USERNAME_FIELD = 'email'
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('full_name', 'phone_number', 'phone_verified')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login',)}),
    )
    
    # ✅ Also define this for the Buyer 'add' page
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password', 'password2'),
        }),
    )
    
    readonly_fields = ('last_login',)
    filter_horizontal = ()