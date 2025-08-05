from .models import Seller, Buyer

class SellerAuthBackend:
    def authenticate(self, request, username=None, password=None, **kwargs):
        phone = kwargs.get('phone', username)
        try:
            user = Seller.objects.get(phone=phone)
            if user.check_password(password):
                return user
        except Seller.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return Seller.objects.get(pk=user_id)
        except Seller.DoesNotExist:
            # Fallback to check Buyer model if Seller not found
            try:
                return Buyer.objects.get(pk=user_id)
            except Buyer.DoesNotExist:
                return None

class BuyerAuthBackend:
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Buyers don't use password auth in our app, but this is for completeness
        email = kwargs.get('email', username)
        try:
            return Buyer.objects.get(email=email)
        except Buyer.DoesNotExist:
            return None
    
    def get_user(self, user_id):
        try:
            return Buyer.objects.get(pk=user_id)
        except Buyer.DoesNotExist:
            # Fallback to check Seller model if Buyer not found
            try:
                return Seller.objects.get(pk=user_id)
            except Seller.DoesNotExist:
                return None