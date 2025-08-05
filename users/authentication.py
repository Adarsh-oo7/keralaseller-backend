from rest_framework.authentication import TokenAuthentication
from .models import SellerToken

class SellerTokenAuthentication(TokenAuthentication):
    """
    Custom token authentication that uses the SellerToken model
    instead of the default Token model.
    """
    model = SellerToken