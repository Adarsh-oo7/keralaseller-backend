# users/backends.py
from django.contrib.auth.backends import BaseBackend
from .models import Seller

class SellerAuthBackend(BaseBackend):
    """
    Custom authentication backend for Seller model using phone number
    """
    def authenticate(self, request, phone=None, password=None, **kwargs):
        print(f"🔍 Backend authenticate called with phone: {phone}")
        
        if phone is None or password is None:
            print("❌ Missing phone or password")
            return None
        
        try:
            seller = Seller.objects.get(phone=phone)
            print(f"✅ Found seller: {seller.phone}")
            
            if seller.check_password(password):
                print(f"✅ Password correct for: {phone}")
                return seller
            else:
                print(f"❌ Password incorrect for: {phone}")
                
        except Seller.DoesNotExist:
            print(f"❌ Seller does not exist: {phone}")
            return None
        
        return None

    def get_user(self, user_id):
        try:
            return Seller.objects.get(pk=user_id)
        except Seller.DoesNotExist:
            return None