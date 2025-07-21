from django.db import models
from django.conf import settings


class UserProfile(models.Model):
    BUSINESS_TYPE_CHOICES = [
        ('retail', 'Retail'),
        ('services', 'Services'),
        ('agriculture', 'Agriculture'),
        ('manufacturing', 'Manufacturing'),
        ('technology', 'Technology'),
        ('hospitality', 'Hospitality'),
        ('healthcare', 'Healthcare'),
        ('education', 'Education'),
        ('finance', 'Finance'),
        ('construction', 'Construction'),
        ('transport', 'Transport & Logistics'),
        ('other', 'Other'),
    ]
    
    EMPLOYEE_COUNT_CHOICES = [
        ('1', '1 employee'),
        ('2-5', '2-5 employees'),
        ('6-10', '6-10 employees'),
        ('11-25', '11-25 employees'),
        ('26-50', '26-50 employees'),
        ('51-100', '51-100 employees'),
        ('100+', '100+ employees'),
    ]
    
    REVENUE_RANGE_CHOICES = [
        ('0-1000', 'ZMW 0 - ZMW 1,000'),
        ('1001-5000', 'ZMW 1,001 - ZMW 5,000'),
        ('5001-10000', 'ZMW 5,001 - ZMW 10,000'),
        ('10001-25000', 'ZMW 10,001 - ZMW 25,000'),
        ('25001-50000', 'ZMW 25,001 - ZMW 50,000'),
        ('50001-100000', 'ZMW 50,001 - ZMW 100,000'),
        ('100001-250000', 'ZMW 100,001 - ZMW 250,000'),
        ('250001-500000', 'ZMW 250,001 - ZMW 500,000'),
        ('500001+', 'ZMW 500,001+'),
    ]
    
    # Link to the custom user model
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    
    # Basic Information
    first_name = models.CharField(max_length=30, default='', help_text="First name")
    last_name = models.CharField(max_length=30, default='', help_text="Last name") 
    full_name = models.CharField(max_length=255, blank=True, help_text="Complete full name (auto-generated from first and last name)")
    business_name = models.CharField(max_length=255, help_text="Name of your business")
    
    # Business Details
    business_type = models.CharField(
        max_length=20,
        choices=BUSINESS_TYPE_CHOICES,
        help_text="Type of business you operate"
    )
    business_city = models.CharField(max_length=100, help_text="City or Town where business is located")
    business_province = models.CharField(max_length=100, help_text="Province where business is located")
    
    # Optional fields
    employee_count = models.CharField(
        max_length=10,
        choices=EMPLOYEE_COUNT_CHOICES,
        blank=True,
        null=True,
        help_text="Number of employees in your business"
    )
    monthly_revenue_range = models.CharField(
        max_length=20,
        choices=REVENUE_RANGE_CHOICES,
        blank=True,
        null=True,
        help_text="Monthly revenue range of your business"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_complete = models.BooleanField(
        default=False,
        help_text="Whether the profile has been completed"
    )
    
    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.full_name} - {self.business_name}"
    
    def save(self, *args, **kwargs):
        # Auto-generate full_name from first_name and last_name
        if self.first_name or self.last_name:
            self.full_name = f"{self.first_name} {self.last_name}".strip()
        
        # Auto-check if profile is complete
        required_fields = [
            self.first_name,
            self.last_name,
            self.business_name,
            self.business_type,
            self.business_city,
            self.business_province
        ]
        self.is_complete = all(field for field in required_fields)
        super().save(*args, **kwargs)
    
    @property
    def email(self):
        """Get email from related user"""
        return self.user.email
    
    @property
    def phone(self):
        """Get phone from related user"""
        return self.user.phone
    
    @property
    def business_location(self):
        """Get formatted business location"""
        return f"{self.business_city}, {self.business_province}"
    
    def get_completion_percentage(self):
        """Calculate profile completion percentage"""
        total_fields = 8  # Total number of profile fields
        completed_fields = 0
        
        # Required fields
        if self.first_name:
            completed_fields += 1
        if self.last_name:
            completed_fields += 1
        if self.business_name:
            completed_fields += 1
        if self.business_type:
            completed_fields += 1
        if self.business_city:
            completed_fields += 1
        if self.business_province:
            completed_fields += 1
        
        # Optional fields
        if self.employee_count:
            completed_fields += 1
        if self.monthly_revenue_range:
            completed_fields += 1
        
        return round((completed_fields / total_fields) * 100)
