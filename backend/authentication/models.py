from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.core.validators import RegexValidator


class CustomUserManager(BaseUserManager):
    def create_user(self, email=None, phone=None, password=None, **extra_fields):
        if not email and not phone:
            raise ValueError('Either email or phone must be provided')
        
        if email:
            email = self.normalize_email(email)
        
        user = self.model(email=email, phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email=None, phone=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, phone, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(validators=[phone_regex], max_length=17, unique=True, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'auth_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email or self.phone or f"User {self.id}"

    def get_full_name(self):
        """Get full name from related profile"""
        if hasattr(self, 'profile') and self.profile.full_name:
            return self.profile.full_name
        return self.email or self.phone or f"User {self.id}"

    def get_short_name(self):
        """Get first name from related profile"""
        if hasattr(self, 'profile') and self.profile.full_name:
            return self.profile.full_name.split()[0] if self.profile.full_name else ""
        return self.email or self.phone or f"User {self.id}"

    @property
    def username(self):
        return self.email or self.phone
