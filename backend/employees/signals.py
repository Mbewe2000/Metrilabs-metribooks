from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import Employee


@receiver(post_save, sender=Employee)
def employee_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for when an Employee is saved
    """
    if created:
        # Log when a new employee is created
        print(f"New employee created: {instance.employee_name} ({instance.employee_id})")
    else:
        # Log when an employee is updated
        print(f"Employee updated: {instance.employee_name} ({instance.employee_id})")


@receiver(pre_delete, sender=Employee)
def employee_pre_delete(sender, instance, **kwargs):
    """
    Signal handler for when an Employee is about to be deleted
    """
    print(f"Employee being deleted: {instance.employee_name} ({instance.employee_id})")
