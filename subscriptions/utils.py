from .models import SellerSubscription

def get_seller_subscription(user):
    return SellerSubscription.objects.filter(seller=user).first()

def can_publish_shop(user):
    subscription = get_seller_subscription(user)
    return subscription and subscription.plan.code in ['basic', 'pro', 'unlimited'] and subscription.is_active()

def has_stock_management(user):
    subscription = get_seller_subscription(user)
    return subscription and subscription.plan.code in ['stock', 'basic', 'pro', 'unlimited'] and subscription.is_active()
