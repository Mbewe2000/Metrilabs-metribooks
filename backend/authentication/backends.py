from django.contrib.auth.backends import BaseBackend
from .models import CustomUser


class EmailPhoneBackend(BaseBackend):
    """
    Custom authentication backend that allows login with either email or phone
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            if '@' in username:
                user = CustomUser.objects.get(email=username)
            else:
                user = CustomUser.objects.get(phone=username)
            
            if user.check_password(password) and user.is_active:
                return user
        except CustomUser.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return None
