from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import WorkRecord, Service


@receiver(pre_save, sender=WorkRecord)
def calculate_work_record_total(sender, instance, **kwargs):
    """
    Calculate total amount before saving work record
    """
    if instance.service:
        if instance.service.pricing_type == 'hourly' and instance.hours_worked:
            instance.total_amount = instance.service.hourly_rate * instance.hours_worked
        elif instance.service.pricing_type == 'fixed':
            instance.total_amount = instance.service.fixed_price * (instance.quantity or 1)


@receiver(post_save, sender=WorkRecord)
def work_record_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for when a WorkRecord is saved
    """
    if created:
        print(f"New work record created: {instance.get_worker_name()} - {instance.service.name} on {instance.date_of_work}")
    else:
        print(f"Work record updated: {instance.get_worker_name()} - {instance.service.name} on {instance.date_of_work}")


@receiver(post_save, sender=Service)
def service_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for when a Service is saved
    """
    if created:
        print(f"New service created: {instance.name} ({instance.get_pricing_type_display()})")
    else:
        print(f"Service updated: {instance.name} ({instance.get_pricing_type_display()})")
