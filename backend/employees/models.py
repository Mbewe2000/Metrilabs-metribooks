from django.db import models
from django.core.validators import RegexValidator


class Employee(models.Model):
    EMPLOYMENT_TYPE_CHOICES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
    ]
    
    employee_id = models.CharField(
        max_length=20, 
        unique=True, 
        help_text="Unique identifier for the employee"
    )
    
    employee_name = models.CharField(
        max_length=100,
        help_text="Full name of the employee"
    )
    
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$', 
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(
        validators=[phone_regex], 
        max_length=17, 
        help_text="Contact phone number"
    )
    
    employment_type = models.CharField(
        max_length=10,
        choices=EMPLOYMENT_TYPE_CHOICES,
        default='full_time',
        help_text="Whether the employee is full-time or part-time"
    )
    
    pay = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Employee pay rate (per hour for part-time, monthly/annual for full-time)"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the employee is currently active"
    )
    
    date_hired = models.DateField(
        auto_now_add=True,
        help_text="Date when the employee was hired"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'employees'
        verbose_name = 'Employee'
        verbose_name_plural = 'Employees'
        ordering = ['employee_name']
    
    def __str__(self):
        return f"{self.employee_id} - {self.employee_name}"
    
    def get_employment_type_display_formatted(self):
        """Returns a formatted display of employment type"""
        return self.get_employment_type_display()
    
    @property
    def is_full_time(self):
        """Returns True if employee is full-time"""
        return self.employment_type == 'full_time'
    
    @property
    def is_part_time(self):
        """Returns True if employee is part-time"""
        return self.employment_type == 'part_time'
