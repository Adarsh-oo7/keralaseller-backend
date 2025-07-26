# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Seller

class SellerAdmin(UserAdmin):
    model = Seller
    list_display = ('phone', 'name', 'shop_name', 'is_active', 'is_staff')
    list_filter = ('is_active', 'is_staff')
    search_fields = ('phone', 'name', 'shop_name', 'email')
    ordering = ('created_at',)

    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        ('Personal info', {'fields': ('name', 'shop_name', 'address', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'password1', 'password2', 'is_active', 'is_staff', 'is_superuser')}
        ),
    )

admin.site.register(Seller, SellerAdmin)
