from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Sum, Count

from .models import ReportSnapshot, ReportTemplate, BusinessMetric


@admin.register(ReportSnapshot)
class ReportSnapshotAdmin(admin.ModelAdmin):
    """
    Admin interface for Report Snapshots
    """
    list_display = [
        'report_type', 'user', 'period_start', 'period_end', 
        'total_income', 'net_profit', 'profit_margin_display', 
        'is_cached', 'generated_at'
    ]
    list_filter = [
        'report_type', 'is_cached', 'period_start', 'generated_at'
    ]
    search_fields = ['user__email', 'report_type']
    readonly_fields = [
        'id', 'generated_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'report_type', 'period_start', 'period_end', 'is_cached')
        }),
        ('Financial Metrics', {
            'fields': (
                'total_income', 'total_expenses', 'net_profit'
            )
        }),
        ('Sales Metrics', {
            'fields': (
                'total_sales_count', 'total_sales_amount', 'average_sale_value'
            )
        }),
        ('Service Metrics', {
            'fields': (
                'total_service_hours', 'total_service_revenue'
            )
        }),
        ('Tax Metrics', {
            'fields': (
                'taxable_income', 'turnover_tax_due'
            )
        }),
        ('Additional Data', {
            'fields': ('additional_data',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'generated_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def profit_margin_display(self, obj):
        """Display profit margin with color coding"""
        margin = obj.get_profit_margin_percentage()
        if margin > 20:
            color = 'green'
        elif margin > 10:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {};">{:.2f}%</span>',
            color, margin
        )
    profit_margin_display.short_description = 'Profit Margin'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('user')


@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    """
    Admin interface for Report Templates
    """
    list_display = [
        'name', 'user', 'frequency', 'auto_generate', 
        'is_active', 'report_types_display', 'created_at'
    ]
    list_filter = ['frequency', 'auto_generate', 'is_active', 'created_at']
    search_fields = ['name', 'user__email', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'name', 'description', 'is_active')
        }),
        ('Report Configuration', {
            'fields': (
                'report_types', 'frequency', 'auto_generate'
            )
        }),
        ('Include Options', {
            'fields': (
                'include_sales', 'include_services', 'include_expenses',
                'include_assets', 'include_tax_analysis'
            )
        }),
        ('Email Settings', {
            'fields': ('email_recipients',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def report_types_display(self, obj):
        """Display report types as a formatted list"""
        if obj.report_types:
            return ', '.join(obj.report_types)
        return '-'
    report_types_display.short_description = 'Report Types'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('user')


@admin.register(BusinessMetric)
class BusinessMetricAdmin(admin.ModelAdmin):
    """
    Admin interface for Business Metrics
    """
    list_display = [
        'metric_type', 'user', 'metric_date', 'value', 
        'percentage_value', 'change_display', 'trend_display'
    ]
    list_filter = [
        'metric_type', 'metric_date', 'created_at'
    ]
    search_fields = ['user__email', 'metric_type', 'notes']
    readonly_fields = [
        'id', 'created_at', 'updated_at'
    ]
    date_hierarchy = 'metric_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'metric_type', 'metric_date')
        }),
        ('Metric Values', {
            'fields': (
                'value', 'percentage_value', 'previous_period_value', 'change_percentage'
            )
        }),
        ('Analysis', {
            'fields': ('notes',)
        }),
        ('Additional Data', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def change_display(self, obj):
        """Display change percentage with color coding"""
        if obj.change_percentage is None:
            return '-'
        
        # Determine if change is positive for this metric type
        is_positive = obj.is_positive_change()
        if is_positive is None:
            color = 'blue'
        elif is_positive:
            color = 'green'
        else:
            color = 'red'
        
        return format_html(
            '<span style="color: {};">{:+.2f}%</span>',
            color, obj.change_percentage
        )
    change_display.short_description = 'Change'
    
    def trend_display(self, obj):
        """Display trend direction with icons"""
        direction = obj.get_trend_direction()
        if direction == 'up':
            return format_html('<span style="color: green;">↗ Up</span>')
        elif direction == 'down':
            return format_html('<span style="color: red;">↘ Down</span>')
        elif direction == 'stable':
            return format_html('<span style="color: blue;">→ Stable</span>')
        else:
            return format_html('<span style="color: gray;">- Neutral</span>')
    trend_display.short_description = 'Trend'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('user')


# Custom admin site configuration
admin.site.site_header = "Metribooks Reports Administration"
admin.site.site_title = "Reports Admin"
admin.site.index_title = "Reports and Analytics Management"


# Register inline admin for quick access
class ReportSnapshotInline(admin.TabularInline):
    """Inline for showing recent report snapshots"""
    model = ReportSnapshot
    extra = 0
    max_num = 5
    readonly_fields = [
        'report_type', 'period_start', 'period_end', 
        'total_income', 'net_profit', 'generated_at'
    ]
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


class BusinessMetricInline(admin.TabularInline):
    """Inline for showing recent business metrics"""
    model = BusinessMetric
    extra = 0
    max_num = 5
    readonly_fields = [
        'metric_type', 'metric_date', 'value', 
        'change_percentage', 'created_at'
    ]
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False
