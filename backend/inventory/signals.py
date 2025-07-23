from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Product, Inventory, StockMovement, StockAlert, ProductCategory
import logging

logger = logging.getLogger('inventory')
User = get_user_model()


@receiver(post_save, sender=User)
def setup_user_inventory(sender, instance, created, **kwargs):
    """
    Set up default product categories when a new user is created
    """
    if created:
        try:
            # Create default categories for the user if they don't exist globally
            default_categories = [
                ('food_beverage', 'Food & Beverage'),
                ('electronics', 'Electronics'),
                ('clothing_accessories', 'Clothing & Accessories'),
                ('health_beauty', 'Health & Beauty'),
                ('home_garden', 'Home & Garden'),
                ('books_stationery', 'Books & Stationery'),
                ('sports_outdoor', 'Sports & Outdoor'),
                ('automotive', 'Automotive'),
                ('toys_games', 'Toys & Games'),
                ('other', 'Other'),
            ]
            
            for category_code, category_name in default_categories:
                ProductCategory.objects.get_or_create(
                    name=category_code,
                    defaults={'description': f'{category_name} products'}
                )
            
            logger.info(f"Inventory setup completed for new user: {instance.email}")
            
        except Exception as e:
            logger.error(f"Error setting up inventory for user {instance.email}: {str(e)}")


@receiver(post_save, sender=Product)
def create_product_inventory(sender, instance, created, **kwargs):
    """
    Create inventory record when a new product is created
    Only create if inventory doesn't already exist (to avoid conflicts with serializer)
    """
    if created:
        try:
            # Check if inventory already exists
            if not hasattr(instance, 'inventory') and not Inventory.objects.filter(product=instance).exists():
                Inventory.objects.create(product=instance)
                logger.info(f"Inventory created for new product: {instance.name} (User: {instance.user.email})")
        except Exception as e:
            logger.error(f"Error creating inventory for product {instance.name}: {str(e)}")


@receiver(post_save, sender=Inventory)
def check_stock_alerts(sender, instance, **kwargs):
    """
    Check and create stock alerts when inventory is updated
    """
    try:
        product = instance.product
        current_stock = instance.quantity_in_stock
        
        # Clear existing unresolved alerts for this product
        StockAlert.objects.filter(
            product=product,
            is_resolved=False
        ).update(is_resolved=True, resolved_at=timezone.now())
        
        # Check for out of stock
        if current_stock <= 0:
            StockAlert.objects.create(
                product=product,
                alert_type='out_of_stock',
                current_stock=current_stock,
                reorder_level=instance.reorder_level
            )
            logger.info(f"Out of stock alert created for: {product.name} (User: {product.user.email})")
        
        # Check for low stock
        elif instance.reorder_level and current_stock <= instance.reorder_level:
            StockAlert.objects.create(
                product=product,
                alert_type='low_stock',
                current_stock=current_stock,
                reorder_level=instance.reorder_level
            )
            logger.info(f"Low stock alert created for: {product.name} (User: {product.user.email})")
            
    except Exception as e:
        logger.error(f"Error checking stock alerts for {instance.product.name}: {str(e)}")


@receiver(post_delete, sender=Product)
def log_product_deletion(sender, instance, **kwargs):
    """
    Log when a product is deleted
    """
    logger.info(f"Product deleted: {instance.name} (ID: {instance.id}) (User: {instance.user.email})")


@receiver(post_save, sender=StockMovement)
def log_stock_movement(sender, instance, created, **kwargs):
    """
    Log stock movements for audit purposes
    """
    if created:
        logger.info(
            f"Stock movement recorded: {instance.product.name} - "
            f"{instance.get_movement_type_display()} - "
            f"Quantity: {instance.quantity} - "
            f"By: {instance.created_by.email if instance.created_by else 'System'} - "
            f"User: {instance.product.user.email}"
        )
