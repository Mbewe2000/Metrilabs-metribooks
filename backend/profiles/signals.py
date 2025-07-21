from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import UserProfile
import logging

logger = logging.getLogger('profiles')

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Create a user profile when a new user is created
    """
    if created:
        try:
            UserProfile.objects.create(user=instance)
            logger.info(f"Profile created automatically for new user: {instance.email}")
        except Exception as e:
            logger.error(f"Error creating profile for user {instance.email}: {str(e)}")


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Save the user profile when the user is saved
    """
    try:
        if hasattr(instance, 'profile'):
            instance.profile.save()
        else:
            # Create profile if it doesn't exist
            UserProfile.objects.get_or_create(user=instance)
            logger.info(f"Profile created for existing user: {instance.email}")
    except Exception as e:
        logger.error(f"Error saving profile for user {instance.email}: {str(e)}")
