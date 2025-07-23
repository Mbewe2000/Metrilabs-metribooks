from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import Sale, SaleItem, SalesReport


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = ('total_price', 'item_name')
    fields = ('item_type', 'product', 'service', 'item_name', 'quantity', 'unit_price', 'discount_amount', 'total_price', 'notes')


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = (
        'sale_number', 'user', 'customer_name', 'sale_date', 
        'total_amount', 'payment_method', 'status', 'is_fully_paid'
    )
    list_filter = (
        'status', 'payment_method', 'sale_date', 'created_at'
    )
    search_fields = (
        'sale_number', 'customer_name', 'customer_phone', 'customer_email',
        'user__email'
    )
    readonly_fields = (
        'id', 'sale_number', 'subtotal', 'total_amount', 'balance_due', 
        'is_fully_paid', 'created_at', 'updated_at'
    )
    fieldsets = (
        ('Sale Information', {
            'fields': ('id', 'sale_number', 'user', 'sale_date', 'status')
        }),
        ('Customer Information', {
            'fields': ('customer_name', 'customer_phone', 'customer_email')
        }),
        ('Financial Details', {
            'fields': (
                'subtotal', 'discount_amount', 'tax_amount', 'total_amount',
                'payment_method', 'payment_reference', 'amount_paid', 
                'change_amount', 'balance_due', 'is_fully_paid'
            )
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    inlines = [SaleItemInline]
    date_hierarchy = 'sale_date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related('items')


@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = (
        'sale_number', 'item_name', 'item_type', 'quantity', 
        'unit_price', 'discount_amount', 'total_price'
    )
    list_filter = ('item_type', 'sale__sale_date', 'sale__status')
    search_fields = (
        'sale__sale_number', 'item_name', 'product__name', 'service__name'
    )
    readonly_fields = ('total_price', 'item_name', 'created_at')
    
    def sale_number(self, obj):
        return obj.sale.sale_number
    sale_number.short_description = 'Sale Number'
    sale_number.admin_order_field = 'sale__sale_number'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'sale', 'product', 'service'
        )


@admin.register(SalesReport)
class SalesReportAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'report_type', 'period_start', 'period_end',
        'total_sales', 'total_revenue', 'generated_at'
    )
    list_filter = ('report_type', 'period_start', 'generated_at')
    search_fields = ('user__email',)
    readonly_fields = (
        'total_sales', 'total_revenue', 'total_discounts', 'total_tax',
        'payment_method_breakdown', 'top_products', 'top_services',
        'generated_at'
    )
    date_hierarchy = 'period_start'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


# Custom admin views for better organization
admin.site.site_header = "MetriBooks Sales Administration"
admin.site.site_title = "Sales Admin"
admin.site.index_title = "Sales Management"
