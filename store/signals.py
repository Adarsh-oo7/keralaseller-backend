from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import Product, StockHistory

@receiver(pre_save, sender=Product)
def capture_old_stock_values(sender, instance, **kwargs):
    """
    Before a product is saved, this signal captures its current stock values
    from the database and attaches them to the instance.
    """
    if instance.pk: # This check ensures the object is being updated, not created
        try:
            old_instance = Product.objects.get(pk=instance.pk)
            instance._old_total_stock = old_instance.total_stock
            instance._old_online_stock = old_instance.online_stock
        except Product.DoesNotExist:
            pass

@receiver(post_save, sender=Product)
def log_stock_changes(sender, instance, created, **kwargs):
    """
    After a product is saved, this signal creates a StockHistory record
    for new products or for any updates to stock levels.
    """
    user = getattr(instance, '_current_user', None)
    note = getattr(instance, '_stock_change_note', None) # Get the note

    if created:
        # Log the initial stock when a new product is created
        StockHistory.objects.create(
            product=instance,
            user=user,
            action=StockHistory.Action.CREATED,
            change_total=instance.total_stock,
            change_online=instance.online_stock,
            note="Initial stock for new product." # Default note for creation
        )
    else:
        # This is an update. Compare the new values with the old ones from pre_save.
        old_total = getattr(instance, '_old_total_stock', instance.total_stock)
        old_online = getattr(instance, '_old_online_stock', instance.online_stock)
        
        change_total = instance.total_stock - old_total
        change_online = instance.online_stock - old_online

        # Only create a log if a stock value actually changed
        if change_total != 0 or change_online != 0:
            StockHistory.objects.create(
                product=instance,
                user=user,
                action=StockHistory.Action.UPDATED,
                change_total=change_total,
                change_online=change_online,
                note=note # ✅ Add the note to the history log
            )