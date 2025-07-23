from django.contrib import admin
from .models import Employee


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = [
        'employee_id', 
        'employee_name', 
        'phone_number', 
        'employment_type', 
        'pay', 
        'is_active',
        'date_hired'
    ]
    list_filter = ['employment_type', 'is_active', 'date_hired']
    search_fields = ['employee_id', 'employee_name', 'phone_number']
    readonly_fields = ['date_hired', 'created_at', 'updated_at']
    ordering = ['employee_name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('employee_id', 'employee_name', 'phone_number')
        }),
        ('Employment Details', {
            'fields': ('employment_type', 'pay', 'is_active')
        }),
        ('Important Dates', {
            'fields': ('date_hired', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Make employee_id readonly when editing existing employee"""
        if obj:  # editing an existing object
            return self.readonly_fields + ('employee_id',)
        return self.readonly_fields
