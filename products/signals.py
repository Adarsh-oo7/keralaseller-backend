from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from .models import Product, StockHistory

@receiver(pre_save, sender=Product)
def capture_old_stock_values(sender, instance, **kwargs):
    """
    Before a product is saved, this signal captures its current stock values
    from the database and attaches them to the instance.
    """
    if instance.pk:  # This check ensures the object is being updated, not created
        try:
            old_instance = Product.objects.get(pk=instance.pk)
            instance._old_total_stock = old_instance.total_stock
            instance._old_online_stock = old_instance.online_stock
        except Product.DoesNotExist:
            instance._old_total_stock = 0
            instance._old_online_stock = 0

@receiver(post_save, sender=Product)
def log_stock_changes(sender, instance, created, **kwargs):
    """
    After a product is saved, this signal creates a StockHistory record
    for new products or for any updates to stock levels.
    """
    # Get user and note from instance attributes
    user = getattr(instance, '_current_user', None)
    note = getattr(instance, '_stock_change_note', None)
    
    # If no user is set, try to get the seller from the product's store
    if not user and instance.store and hasattr(instance.store, 'seller'):
        user = instance.store.seller
    
    # Set default note if none provided
    if not note:
        note = "Stock change via system" if not created else "Initial stock for new product"

    if created:
        # Log the initial stock when a new product is created
        try:
            if user:
                # Get the content type for the user (seller)
                content_type = ContentType.objects.get_for_model(user)
                
                StockHistory.objects.create(
                    product=instance,
                    user_content_type=content_type,
                    user_object_id=user.pk,
                    action=StockHistory.Action.CREATED,
                    change_total=instance.total_stock,
                    change_online=instance.online_stock,
                    note=note
                )
                print(f"✅ StockHistory created for new product: {instance.name}")
            else:
                print(f"⚠️ Warning: No user found for product {instance.name}, skipping StockHistory creation")
        except Exception as e:
            print(f"❌ Error creating StockHistory for new product: {e}")
    else:
        # This is an update. Compare the new values with the old ones from pre_save.
        old_total = getattr(instance, '_old_total_stock', instance.total_stock)
        old_online = getattr(instance, '_old_online_stock', instance.online_stock)
        
        change_total = instance.total_stock - old_total
        change_online = instance.online_stock - old_online

        # Only create a log if a stock value actually changed
        if change_total != 0 or change_online != 0:
            try:
                if user:
                    # Get the content type for the user (seller)
                    content_type = ContentType.objects.get_for_model(user)
                    
                    StockHistory.objects.create(
                        product=instance,
                        user_content_type=content_type,
                        user_object_id=user.pk,
                        action=StockHistory.Action.UPDATED,
                        change_total=change_total,
                        change_online=change_online,
                        note=note or f"Stock updated: Total {change_total:+d}, Online {change_online:+d}"
                    )
                    print(f"✅ StockHistory updated for product: {instance.name}")
                else:
                    print(f"⚠️ Warning: No user found for product update {instance.name}")
            except Exception as e:
                print(f"❌ Error creating StockHistory for update: {e}")
