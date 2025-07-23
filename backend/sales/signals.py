from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from decimal import Decimal
import logging

from .models import Sale, SaleItem

logger = logging.getLogger('sales')


@receiver(post_save, sender=Sale)
def sale_post_save(sender, instance, created, **kwargs):
    """Handle sale creation/update"""
    if created:
        logger.info(f"New sale created: {instance.sale_number} for user {instance.user.email}")
    else:
        logger.info(f"Sale updated: {instance.sale_number} for user {instance.user.email}")


@receiver(post_save, sender=SaleItem)
def sale_item_post_save(sender, instance, created, **kwargs):
    """Handle sale item creation/update and update sale totals"""
    if created:
        # Recalculate sale totals when items are added
        with transaction.atomic():
            sale = instance.sale
            
            # Calculate new subtotal from all items
            subtotal = sum(item.total_price for item in sale.items.all())
            
            # Update sale totals
            total_amount = subtotal + sale.tax_amount - sale.discount_amount
            
            Sale.objects.filter(pk=sale.pk).update(
                subtotal=subtotal,
                total_amount=max(total_amount, Decimal('0.01'))  # Ensure minimum total
            )
            
            # Update inventory if this is a product sale
            if instance.item_type == 'product' and instance.product and hasattr(instance.product, 'inventory'):
                inventory = instance.product.inventory
                
                # Get stock quantities for movement record
                quantity_before = inventory.quantity_in_stock
                
                # Reduce stock
                inventory.quantity_in_stock -= instance.quantity
                inventory.save()
                
                quantity_after = inventory.quantity_in_stock
                
                # Create inventory movement record
                from inventory.models import StockMovement
                
                StockMovement.objects.create(
                    product=instance.product,
                    movement_type='sale',
                    quantity=-instance.quantity,  # Negative for outbound
                    quantity_before=quantity_before,
                    quantity_after=quantity_after,
                    reference_number=sale.sale_number,
                    notes=f"Sale #{sale.sale_number} - {instance.item_name}",
                    created_by=sale.user
                )
                
                logger.info(f"Inventory updated: {instance.product.name} stock reduced by {instance.quantity}")


@receiver(post_delete, sender=SaleItem)
def sale_item_post_delete(sender, instance, **kwargs):
    """Handle sale item deletion and update sale totals"""
    try:
        sale = instance.sale
        
        # Recalculate sale totals when items are removed
        with transaction.atomic():
            # Calculate new subtotal from remaining items
            subtotal = sum(item.total_price for item in sale.items.all())
            
            # Update sale totals
            total_amount = subtotal + sale.tax_amount - sale.discount_amount
            
            Sale.objects.filter(pk=sale.pk).update(
                subtotal=subtotal,
                total_amount=max(total_amount, Decimal('0.01'))  # Ensure minimum total
            )
            
            # If this was a product sale, reverse the inventory movement
            if instance.item_type == 'product' and instance.product and hasattr(instance.product, 'inventory'):
                inventory = instance.product.inventory
                
                # Get stock quantities for movement record
                quantity_before = inventory.quantity_in_stock
                
                # Restore stock
                inventory.quantity_in_stock += instance.quantity
                inventory.save()
                
                quantity_after = inventory.quantity_in_stock
                
                # Create reverse inventory movement
                from inventory.models import StockMovement
                
                StockMovement.objects.create(
                    product=instance.product,
                    movement_type='return',
                    quantity=instance.quantity,  # Positive for inbound
                    quantity_before=quantity_before,
                    quantity_after=quantity_after,
                    reference_number=f"REV-{sale.sale_number}",
                    notes=f"Sale item removed from #{sale.sale_number}",
                    created_by=sale.user
                )
                
    except Sale.DoesNotExist:
        # Sale might have been deleted, ignore
        pass
