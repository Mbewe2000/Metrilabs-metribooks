from django.contrib import admin
from .models import ServiceCategory, Service, WorkRecord


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['name']


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'pricing_type', 'hourly_rate', 
        'fixed_price', 'is_active', 'created_at'
    ]
    list_filter = ['pricing_type', 'is_active', 'category', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category', 'description')
        }),
        ('Pricing', {
            'fields': ('pricing_type', 'hourly_rate', 'fixed_price')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_form(self, request, obj=None, **kwargs):
        """Customize form based on pricing type"""
        form = super().get_form(request, obj, **kwargs)
        return form


@admin.register(WorkRecord)
class WorkRecordAdmin(admin.ModelAdmin):
    list_display = [
        'get_worker_name', 'service', 'date_of_work', 
        'hours_worked', 'quantity', 'total_amount', 'worker_type'
    ]
    list_filter = ['worker_type', 'date_of_work', 'service', 'employee']
    search_fields = [
        'service__name', 'employee__employee_name', 
        'owner_name', 'notes'
    ]
    readonly_fields = ['total_amount', 'created_at', 'updated_at']
    date_hierarchy = 'date_of_work'
    ordering = ['-date_of_work', '-created_at']
    
    fieldsets = (
        ('Worker Information', {
            'fields': ('worker_type', 'employee', 'owner_name')
        }),
        ('Work Details', {
            'fields': ('service', 'date_of_work', 'hours_worked', 'quantity', 'notes')
        }),
        ('Calculated Fields', {
            'fields': ('total_amount',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_worker_name(self, obj):
        """Display worker name in admin list"""
        return obj.get_worker_name()
    get_worker_name.short_description = 'Worker'
    get_worker_name.admin_order_field = 'employee__employee_name'
    
    def get_form(self, request, obj=None, **kwargs):
        """Customize form behavior"""
        form = super().get_form(request, obj, **kwargs)
        return form
