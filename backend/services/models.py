from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal
from employees.models import Employee


class ServiceCategory(models.Model):
    """Categories for organizing services"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'service_categories'
        verbose_name = 'Service Category'
        verbose_name_plural = 'Service Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Service(models.Model):
    """Services or work types offered by the business"""
    PRICING_TYPE_CHOICES = [
        ('hourly', 'Hourly Rate'),
        ('fixed', 'Fixed Price'),
    ]
    
    name = models.CharField(
        max_length=200,
        help_text="Name of the service (e.g., Cleaning, Delivery, Haircut, Nails)"
    )
    
    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='services'
    )
    
    pricing_type = models.CharField(
        max_length=10,
        choices=PRICING_TYPE_CHOICES,
        default='hourly',
        help_text="Whether this service is charged hourly or at a fixed price"
    )
    
    hourly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        null=True,
        blank=True,
        help_text="Rate per hour in ZMW (for hourly services)"
    )
    
    fixed_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        null=True,
        blank=True,
        help_text="Fixed price in ZMW (for fixed-price services)"
    )
    
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'services'
        verbose_name = 'Service'
        verbose_name_plural = 'Services'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_pricing_type_display()})"
    
    def clean(self):
        """Validate that either hourly_rate or fixed_price is set based on pricing_type"""
        from django.core.exceptions import ValidationError
        
        if self.pricing_type == 'hourly' and not self.hourly_rate:
            raise ValidationError("Hourly rate is required for hourly services")
        elif self.pricing_type == 'fixed' and not self.fixed_price:
            raise ValidationError("Fixed price is required for fixed-price services")
    
    @property
    def price_display(self):
        """Return formatted price based on pricing type"""
        if self.pricing_type == 'hourly':
            return f"ZMW {self.hourly_rate}/hour"
        else:
            return f"ZMW {self.fixed_price}"


class WorkRecord(models.Model):
    """Records of work/services performed"""
    WORKER_TYPE_CHOICES = [
        ('employee', 'Employee'),
        ('owner', 'Owner/Self'),
    ]
    
    # Worker information
    worker_type = models.CharField(
        max_length=10,
        choices=WORKER_TYPE_CHOICES,
        default='employee'
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='work_records',
        help_text="Business owner who recorded this work",
        default=1  # Temporary default for migration
    )
    
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='work_records',
        help_text="Employee who performed the work (if worker_type is 'employee')"
    )
    
    owner_name = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Owner name (if worker_type is 'owner')"
    )
    
    # Service information
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='work_records'
    )
    
    # Work details
    date_of_work = models.DateField(
        help_text="Date when the work was performed"
    )
    
    hours_worked = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        null=True,
        blank=True,
        help_text="Hours worked (for hourly services)"
    )
    
    quantity = models.PositiveIntegerField(
        default=1,
        help_text="Number of services performed (for fixed-price services)"
    )
    
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Total amount for this work record"
    )
    
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('paid', 'Paid'),
            ('cancelled', 'Cancelled'),
        ],
        default='pending',
        help_text="Payment status for this work record"
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes about the work performed"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'work_records'
        verbose_name = 'Work Record'
        verbose_name_plural = 'Work Records'
        ordering = ['-date_of_work', '-created_at']
    
    def __str__(self):
        worker_name = self.get_worker_name()
        return f"{worker_name} - {self.service.name} on {self.date_of_work}"
    
    def get_worker_name(self):
        """Return the name of the worker"""
        if self.worker_type == 'employee' and self.employee:
            return self.employee.employee_name
        elif self.worker_type == 'owner':
            return self.owner_name or "Owner"
        return "Unknown"
    
    def clean(self):
        """Validate work record data"""
        from django.core.exceptions import ValidationError
        
        # Validate worker information
        if self.worker_type == 'employee' and not self.employee:
            raise ValidationError("Employee must be selected for employee work records")
        elif self.worker_type == 'owner' and not self.owner_name:
            raise ValidationError("Owner name is required for owner work records")
        
        # Validate work details based on service pricing type
        if self.service:
            if self.service.pricing_type == 'hourly' and not self.hours_worked:
                raise ValidationError("Hours worked is required for hourly services")
            elif self.service.pricing_type == 'fixed' and self.quantity < 1:
                raise ValidationError("Quantity must be at least 1 for fixed-price services")
    
    def save(self, *args, **kwargs):
        """Calculate total amount before saving"""
        if self.service:
            if self.service.pricing_type == 'hourly' and self.hours_worked:
                self.total_amount = self.service.hourly_rate * self.hours_worked
            elif self.service.pricing_type == 'fixed':
                self.total_amount = self.service.fixed_price * self.quantity
        
        super().save(*args, **kwargs)
    
    @property
    def worker_display(self):
        """Return formatted worker display"""
        return f"{self.get_worker_name()} ({self.get_worker_type_display()})"
