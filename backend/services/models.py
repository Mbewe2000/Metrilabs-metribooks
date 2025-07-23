from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.utils import timezone

User = get_user_model()


class ServiceCategory(models.Model):
    """Categories for different types of services"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Service Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Service(models.Model):
    """Service definitions for each business"""
    PRICING_TYPES = [
        ('hourly', 'Hourly Rate'),
        ('fixed', 'Fixed Price'),
        ('both', 'Both (Hourly & Fixed)'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=200, help_text="e.g., Haircut, Cleaning, Delivery, Tailoring")
    description = models.TextField(blank=True, help_text="Optional description of the service")
    category = models.ForeignKey(
        ServiceCategory, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="e.g., Labor, Consultancy, Repairs"
    )
    
    # Pricing options
    pricing_type = models.CharField(
        max_length=10, 
        choices=PRICING_TYPES, 
        default='hourly',
        help_text="How this service is priced"
    )
    hourly_rate = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Rate per hour in ZMW"
    )
    fixed_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Fixed price for the service in ZMW"
    )
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        unique_together = ['user', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.user.email})"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        
        if self.pricing_type == 'hourly' and not self.hourly_rate:
            raise ValidationError("Hourly rate is required for hourly pricing")
        if self.pricing_type == 'fixed' and not self.fixed_price:
            raise ValidationError("Fixed price is required for fixed pricing")
        if self.pricing_type == 'both' and not (self.hourly_rate and self.fixed_price):
            raise ValidationError("Both hourly rate and fixed price are required for 'both' pricing type")
    
    def get_display_price(self):
        """Get a formatted display of the pricing"""
        if self.pricing_type == 'hourly':
            return f"ZMW {self.hourly_rate}/hour"
        elif self.pricing_type == 'fixed':
            return f"ZMW {self.fixed_price} (fixed)"
        elif self.pricing_type == 'both':
            return f"ZMW {self.hourly_rate}/hour or ZMW {self.fixed_price} (fixed)"
        return "Price not set"


class Worker(models.Model):
    """Workers/Employees who can perform services"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workers')
    name = models.CharField(max_length=200)
    employee_id = models.CharField(max_length=50, blank=True, help_text="Optional employee ID")
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    
    # Worker status
    is_owner = models.BooleanField(default=False, help_text="Is this the business owner?")
    is_active = models.BooleanField(default=True)
    
    # Services this worker can perform
    services = models.ManyToManyField(Service, blank=True, help_text="Services this worker can perform")
    
    # Metadata
    hired_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_owner', 'name']
        unique_together = ['user', 'name']
    
    def __str__(self):
        owner_indicator = " (Owner)" if self.is_owner else ""
        return f"{self.name}{owner_indicator}"
    
    def get_services_list(self):
        """Get comma-separated list of services this worker can perform"""
        return ", ".join([service.name for service in self.services.all()])


class ServiceRecord(models.Model):
    """Record of work performed by workers"""
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('partially_paid', 'Partially Paid'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='service_records')
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE, related_name='service_records')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='service_records')
    
    # Work details
    date_performed = models.DateField(default=timezone.now)
    start_time = models.TimeField(null=True, blank=True, help_text="Start time (for hourly services)")
    end_time = models.TimeField(null=True, blank=True, help_text="End time (for hourly services)")
    hours_worked = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Total hours worked (can be manually entered or auto-calculated)"
    )
    
    # Pricing details
    used_fixed_price = models.BooleanField(default=False, help_text="Was fixed pricing used?")
    hourly_rate_used = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Hourly rate used for this record (may differ from service's current rate)"
    )
    fixed_price_used = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Fixed price used for this record"
    )
    total_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Total amount for this work"
    )
    
    # Additional details
    customer_name = models.CharField(max_length=200, blank=True, help_text="Customer who received the service")
    notes = models.TextField(blank=True, help_text="Additional notes about the work performed")
    reference_number = models.CharField(max_length=100, blank=True, help_text="Reference number or invoice ID")
    
    # Payment tracking
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    amount_paid = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date_performed', '-created_at']
    
    def __str__(self):
        return f"{self.worker.name} - {self.service.name} ({self.date_performed})"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Validate that worker can perform this service
        if self.worker.services.exists() and self.service not in self.worker.services.all():
            raise ValidationError(f"{self.worker.name} is not assigned to perform {self.service.name}")
        
        # Validate pricing logic
        if not self.used_fixed_price and not self.hours_worked:
            raise ValidationError("Hours worked is required when not using fixed pricing")
        
        if self.used_fixed_price and not self.fixed_price_used:
            raise ValidationError("Fixed price is required when using fixed pricing")
        
        if not self.used_fixed_price and not self.hourly_rate_used:
            raise ValidationError("Hourly rate is required when not using fixed pricing")
    
    def save(self, *args, **kwargs):
        # Auto-calculate total amount if not provided
        if not self.total_amount:
            self.calculate_total_amount()
        
        # Auto-calculate hours from start/end time if provided
        if self.start_time and self.end_time and not self.hours_worked:
            self.calculate_hours_worked()
        
        # Set default rates from service if not provided
        if not self.hourly_rate_used and self.service.hourly_rate:
            self.hourly_rate_used = self.service.hourly_rate
        
        if not self.fixed_price_used and self.service.fixed_price:
            self.fixed_price_used = self.service.fixed_price
        
        super().save(*args, **kwargs)
    
    def calculate_hours_worked(self):
        """Calculate hours worked from start and end time"""
        if self.start_time and self.end_time:
            from datetime import datetime, timedelta
            
            start = datetime.combine(self.date_performed, self.start_time)
            end = datetime.combine(self.date_performed, self.end_time)
            
            # Handle overnight work (end time next day)
            if end < start:
                end += timedelta(days=1)
            
            duration = end - start
            self.hours_worked = Decimal(str(duration.total_seconds() / 3600))
    
    def calculate_total_amount(self):
        """Calculate total amount based on pricing type and hours/fixed price"""
        if self.used_fixed_price and self.fixed_price_used:
            self.total_amount = self.fixed_price_used
        elif self.hours_worked and self.hourly_rate_used:
            self.total_amount = self.hours_worked * self.hourly_rate_used
        else:
            self.total_amount = Decimal('0.00')
    
    @property
    def remaining_balance(self):
        """Calculate remaining balance to be paid"""
        return self.total_amount - self.amount_paid
    
    @property
    def is_fully_paid(self):
        """Check if the service is fully paid"""
        return self.amount_paid >= self.total_amount
    
    def update_payment_status(self):
        """Update payment status based on amount paid"""
        if self.amount_paid == 0:
            self.payment_status = 'pending'
        elif self.amount_paid >= self.total_amount:
            self.payment_status = 'paid'
        else:
            self.payment_status = 'partially_paid'


class WorkerPerformance(models.Model):
    """Monthly performance summary for workers"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE)
    
    # Period
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField()  # 1-12
    
    # Performance metrics
    total_hours_worked = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    total_services_performed = models.PositiveIntegerField(default=0)
    total_revenue_generated = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    average_hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Service breakdown (JSON field for detailed service counts)
    services_breakdown = models.JSONField(default=dict, help_text="Breakdown of services performed")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'worker', 'year', 'month']
        ordering = ['-year', '-month', 'worker__name']
    
    def __str__(self):
        return f"{self.worker.name} - {self.year}-{self.month:02d}"
    
    @classmethod
    def generate_for_period(cls, user, year, month):
        """Generate performance records for all workers for a given period"""
        from django.db.models import Sum, Count, Avg
        from calendar import monthrange
        
        # Get start and end dates for the month
        start_date = timezone.datetime(year, month, 1).date()
        _, last_day = monthrange(year, month)
        end_date = timezone.datetime(year, month, last_day).date()
        
        workers = Worker.objects.filter(user=user, is_active=True)
        
        for worker in workers:
            # Get service records for this worker in this period
            records = ServiceRecord.objects.filter(
                user=user,
                worker=worker,
                date_performed__gte=start_date,
                date_performed__lte=end_date
            )
            
            if records.exists():
                # Calculate metrics
                total_hours = records.aggregate(
                    total=Sum('hours_worked')
                )['total'] or Decimal('0.00')
                
                total_services = records.count()
                
                total_revenue = records.aggregate(
                    total=Sum('total_amount')
                )['total'] or Decimal('0.00')
                
                avg_rate = records.aggregate(
                    avg=Avg('hourly_rate_used')
                )['avg'] or Decimal('0.00')
                
                # Service breakdown
                services_breakdown = {}
                for record in records:
                    service_name = record.service.name
                    if service_name in services_breakdown:
                        services_breakdown[service_name] += 1
                    else:
                        services_breakdown[service_name] = 1
                
                # Create or update performance record
                performance, created = cls.objects.update_or_create(
                    user=user,
                    worker=worker,
                    year=year,
                    month=month,
                    defaults={
                        'total_hours_worked': total_hours,
                        'total_services_performed': total_services,
                        'total_revenue_generated': total_revenue,
                        'average_hourly_rate': avg_rate,
                        'services_breakdown': services_breakdown,
                    }
                )
                
                return performance
        
        return None
