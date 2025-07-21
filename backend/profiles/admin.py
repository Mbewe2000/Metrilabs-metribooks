from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'full_name',
        'business_name',
        'email',
        'phone',
        'business_type',
        'business_location',
        'is_complete',
        'created_at'
    )
    list_filter = (
        'business_type',
        'business_province',
        'is_complete',
        'employee_count',
        'monthly_revenue_range',
        'created_at'
    )
    search_fields = (
        'first_name',
        'last_name',
        'full_name',
        'business_name',
        'user__email',
        'user__phone',
        'business_city',
        'business_province'
    )
    readonly_fields = (
        'user',
        'email',
        'phone',
        'full_name',
        'business_location',
        'is_complete',
        'created_at',
        'updated_at'
    )
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'email', 'phone')
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'full_name')
        }),
        ('Business Information', {
            'fields': ('business_name',)
        }),
        ('Business Details', {
            'fields': (
                'business_type',
                'business_city',
                'business_province',
                'business_location'
            )
        }),
        ('Optional Business Information', {
            'fields': ('employee_count', 'monthly_revenue_range'),
            'classes': ('collapse',)
        }),
        ('Status & Dates', {
            'fields': ('is_complete', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    ordering = ('-created_at',)
    
    def email(self, obj):
        return obj.user.email
    email.short_description = 'Email Address'
    
    def phone(self, obj):
        return obj.user.phone
    phone.short_description = 'Phone Number'
    
    def has_add_permission(self, request):
        # Profiles should be created automatically when users register
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of profiles from admin
        return False
