from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from .models import Buyer

class BuyerJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that works with Buyer model
    """
    
    def get_user(self, validated_token):
        """
        Override to get Buyer instance instead of default User
        """
        try:
            user_id = validated_token['user_id']
            user = Buyer.objects.get(id=user_id)
            return user
        except Buyer.DoesNotExist:
            raise InvalidToken('No user matching this token was found.')
