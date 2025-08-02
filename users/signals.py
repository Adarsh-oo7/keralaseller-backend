from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Seller
from store.models import StoreProfile

@receiver(post_save, sender=Seller)
def create_store_profile_for_seller(sender, instance, created, **kwargs):
    """
    Automatically create a StoreProfile when a new Seller is created.
    """
    if created:
        store_name = instance.shop_name or f"{instance.name}'s Store"
        if not store_name.strip():
            store_name = f"Store for {instance.phone}"
        StoreProfile.objects.create(seller=instance, name=store_name)