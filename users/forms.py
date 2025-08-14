from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Seller

class SellerCreationForm(UserCreationForm):
    """A form for creating new sellers in the admin."""
    class Meta(UserCreationForm.Meta):
        model = Seller
        fields = ('phone',)

class SellerChangeForm(UserChangeForm):
    """A form for updating seller profiles in the admin."""
    class Meta(UserChangeForm.Meta):
        model = Seller
        fields = ('phone', 'name', 'shop_name', 'email', 'address', 'is_active', 'is_staff')