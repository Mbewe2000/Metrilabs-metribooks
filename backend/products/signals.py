from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Product, ProductInventory
import logging

logger = logging.getLogger('products')


@receiver(post_save, sender=Product)
def create_product_inventory(sender, instance, created, **kwargs):
    """
    Create a product inventory record when a new product is created
    """
    if created:
        try:
            ProductInventory.objects.create(product=instance)
            logger.info(f"Inventory record created for product: {instance.name}")
        except Exception as e:
            logger.error(f"Error creating inventory for product {instance.name}: {str(e)}")


@receiver(post_save, sender=Product)
def save_product_inventory(sender, instance, **kwargs):
    """
    Ensure the product has an inventory record
    """
    try:
        if not hasattr(instance, 'inventory'):
            ProductInventory.objects.get_or_create(product=instance)
            logger.info(f"Inventory record ensured for product: {instance.name}")
    except Exception as e:
        logger.error(f"Error ensuring inventory for product {instance.name}: {str(e)}")
