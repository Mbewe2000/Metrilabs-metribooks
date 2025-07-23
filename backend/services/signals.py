from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import ServiceCategory, Service, Worker, ServiceRecord, WorkerPerformance
import logging

logger = logging.getLogger('services')
User = get_user_model()


@receiver(post_save, sender=User)
def setup_user_services(sender, instance, created, **kwargs):
    """
    Set up default service categories when a new user is created
    """
    if created:
        try:
            # Create default service categories if they don't exist globally
            default_categories = [
                ('labor', 'Labor Services'),
                ('consultancy', 'Consultancy Services'),
                ('repairs', 'Repair Services'),
                ('beauty_wellness', 'Beauty & Wellness'),
                ('cleaning', 'Cleaning Services'),
                ('delivery_transport', 'Delivery & Transport'),
                ('maintenance', 'Maintenance Services'),
                ('professional', 'Professional Services'),
                ('creative', 'Creative Services'),
                ('other', 'Other Services'),
            ]
            
            created_categories = []
            for category_code, category_name in default_categories:
                category, was_created = ServiceCategory.objects.get_or_create(
                    name=category_code,
                    defaults={'description': f'{category_name} category'}
                )
                if was_created:
                    created_categories.append(category_name)
            
            # Create a default "Business Owner" worker for the new user
            Worker.objects.get_or_create(
                user=instance,
                name=f"{instance.email} (Owner)",
                defaults={
                    'is_owner': True,
                    'is_active': True,
                    'hired_date': timezone.now().date()
                }
            )
            
            logger.info(f"Services setup completed for new user: {instance.email}")
            if created_categories:
                logger.info(f"Created categories: {', '.join(created_categories)}")
            
        except Exception as e:
            logger.error(f"Error setting up services for user {instance.email}: {str(e)}")


@receiver(post_save, sender=ServiceRecord)
def update_worker_performance(sender, instance, created, **kwargs):
    """
    Update worker performance when a service record is created or updated
    """
    if created:
        try:
            # Generate/update performance record for the month
            WorkerPerformance.generate_for_period(
                instance.user,
                instance.date_performed.year,
                instance.date_performed.month
            )
            
            logger.info(
                f"Performance updated for worker {instance.worker.name} - "
                f"{instance.date_performed.year}-{instance.date_performed.month:02d}"
            )
            
        except Exception as e:
            logger.error(f"Error updating worker performance: {str(e)}")


@receiver(post_save, sender=ServiceRecord)
def log_service_record_creation(sender, instance, created, **kwargs):
    """
    Log service record creation for audit purposes
    """
    if created:
        logger.info(
            f"Service record created: {instance.worker.name} - "
            f"{instance.service.name} - "
            f"Amount: ZMW {instance.total_amount} - "
            f"Date: {instance.date_performed} - "
            f"User: {instance.user.email}"
        )


@receiver(post_delete, sender=Service)
def log_service_deletion(sender, instance, **kwargs):
    """
    Log when a service is deleted
    """
    logger.info(
        f"Service deleted: {instance.name} (ID: {instance.id}) "
        f"(User: {instance.user.email})"
    )


@receiver(post_delete, sender=Worker)
def log_worker_deletion(sender, instance, **kwargs):
    """
    Log when a worker is deleted
    """
    logger.info(
        f"Worker deleted: {instance.name} (ID: {instance.id}) "
        f"(User: {instance.user.email})"
    )


@receiver(post_delete, sender=ServiceRecord)
def log_service_record_deletion(sender, instance, **kwargs):
    """
    Log when a service record is deleted and update performance
    """
    try:
        logger.info(
            f"Service record deleted: {instance.worker.name} - "
            f"{instance.service.name} - "
            f"Date: {instance.date_performed} - "
            f"Amount: ZMW {instance.total_amount} - "
            f"User: {instance.user.email}"
        )
        
        # Update worker performance after deletion
        WorkerPerformance.generate_for_period(
            instance.user,
            instance.date_performed.year,
            instance.date_performed.month
        )
        
    except Exception as e:
        logger.error(f"Error handling service record deletion: {str(e)}")


@receiver(post_save, sender=Worker)
def log_worker_creation(sender, instance, created, **kwargs):
    """
    Log worker creation
    """
    if created:
        logger.info(
            f"Worker created: {instance.name} "
            f"{'(Owner)' if instance.is_owner else '(Employee)'} - "
            f"User: {instance.user.email}"
        )
