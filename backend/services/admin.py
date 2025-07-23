from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import ServiceCategory, Service, Worker, ServiceRecord, WorkerPerformance

User = get_user_model()


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']


class ServiceRecordInline(admin.TabularInline):
    model = ServiceRecord
    extra = 0
    readonly_fields = ['total_amount', 'remaining_balance', 'is_fully_paid']
    fields = [
        'date_performed', 'service', 'hours_worked', 'used_fixed_price',
        'total_amount', 'payment_status', 'amount_paid'
    ]


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'user', 'category', 'pricing_type', 'hourly_rate', 
        'fixed_price', 'is_active', 'created_at'
    ]
    list_filter = ['pricing_type', 'category', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'name', 'description', 'category', 'is_active')
        }),
        ('Pricing', {
            'fields': ('pricing_type', 'hourly_rate', 'fixed_price')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user" and not request.user.is_superuser:
            kwargs["queryset"] = User.objects.filter(id=request.user.id)
            kwargs["initial"] = request.user.id
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'user', 'employee_id', 'is_owner', 'is_active', 
        'services_count', 'hired_date', 'created_at'
    ]
    list_filter = ['is_owner', 'is_active', 'hired_date', 'created_at']
    search_fields = ['name', 'employee_id', 'phone', 'email', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['services']
    inlines = [ServiceRecordInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'name', 'employee_id', 'phone', 'email')
        }),
        ('Status', {
            'fields': ('is_owner', 'is_active', 'hired_date')
        }),
        ('Services', {
            'fields': ('services',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def services_count(self, obj):
        return obj.services.count()
    services_count.short_description = 'Services Count'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user" and not request.user.is_superuser:
            kwargs["queryset"] = User.objects.filter(id=request.user.id)
            kwargs["initial"] = request.user.id
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "services" and not request.user.is_superuser:
            kwargs["queryset"] = Service.objects.filter(user=request.user)
        return super().formfield_for_manytomany(db_field, request, **kwargs)


@admin.register(ServiceRecord)
class ServiceRecordAdmin(admin.ModelAdmin):
    list_display = [
        'date_performed', 'worker', 'service', 'customer_name',
        'hours_worked', 'total_amount', 'payment_status', 'created_at'
    ]
    list_filter = [
        'payment_status', 'used_fixed_price', 'date_performed', 'created_at'
    ]
    search_fields = [
        'customer_name', 'reference_number', 'notes',
        'worker__name', 'service__name', 'user__email'
    ]
    readonly_fields = [
        'remaining_balance', 'is_fully_paid', 'created_at', 'updated_at'
    ]
    date_hierarchy = 'date_performed'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'worker', 'service', 'date_performed', 'customer_name')
        }),
        ('Work Details', {
            'fields': (
                'start_time', 'end_time', 'hours_worked', 'notes', 'reference_number'
            )
        }),
        ('Pricing', {
            'fields': (
                'used_fixed_price', 'hourly_rate_used', 'fixed_price_used', 'total_amount'
            )
        }),
        ('Payment', {
            'fields': (
                'payment_status', 'amount_paid', 'remaining_balance', 'is_fully_paid'
            )
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            if db_field.name == "user":
                kwargs["queryset"] = User.objects.filter(id=request.user.id)
                kwargs["initial"] = request.user.id
            elif db_field.name == "worker":
                kwargs["queryset"] = Worker.objects.filter(user=request.user)
            elif db_field.name == "service":
                kwargs["queryset"] = Service.objects.filter(user=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(WorkerPerformance)
class WorkerPerformanceAdmin(admin.ModelAdmin):
    list_display = [
        'worker', 'year', 'month', 'total_services_performed',
        'total_hours_worked', 'total_revenue_generated', 'average_hourly_rate'
    ]
    list_filter = ['year', 'month', 'worker']
    search_fields = ['worker__name', 'user__email']
    readonly_fields = [
        'total_hours_worked', 'total_services_performed', 'total_revenue_generated',
        'average_hourly_rate', 'services_breakdown', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Period', {
            'fields': ('user', 'worker', 'year', 'month')
        }),
        ('Performance Metrics', {
            'fields': (
                'total_hours_worked', 'total_services_performed',
                'total_revenue_generated', 'average_hourly_rate'
            )
        }),
        ('Service Breakdown', {
            'fields': ('services_breakdown',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            if db_field.name == "user":
                kwargs["queryset"] = User.objects.filter(id=request.user.id)
                kwargs["initial"] = request.user.id
            elif db_field.name == "worker":
                kwargs["queryset"] = Worker.objects.filter(user=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
