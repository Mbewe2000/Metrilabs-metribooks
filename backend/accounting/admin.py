from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from .models import (
    ExpenseCategory, Expense, AssetCategory, Asset,
    IncomeRecord, TurnoverTaxRecord, FinancialSummary
)


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'get_display_name', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    
    def get_display_name(self, obj):
        return obj.get_name_display()
    get_display_name.short_description = 'Display Name'


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'user', 'category', 'amount', 'expense_date',
        'payment_status', 'is_overdue', 'created_at'
    ]
    list_filter = [
        'category', 'expense_type', 'payment_status', 'expense_date',
        'created_at'
    ]
    search_fields = ['name', 'vendor', 'reference_number', 'user__email']
    date_hierarchy = 'expense_date'
    readonly_fields = ['id', 'created_at', 'updated_at', 'is_overdue']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'name', 'category', 'amount')
        }),
        ('Expense Details', {
            'fields': ('expense_type', 'recurrence', 'expense_date', 'due_date')
        }),
        ('Payment Information', {
            'fields': ('payment_status', 'payment_date', 'vendor', 'reference_number')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at', 'is_overdue'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'category')
    
    def is_overdue(self, obj):
        if obj.is_overdue:
            return format_html('<span style="color: red;">Yes</span>')
        return format_html('<span style="color: green;">No</span>')
    is_overdue.short_description = 'Overdue'


@admin.register(AssetCategory)
class AssetCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'get_display_name', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    
    def get_display_name(self, obj):
        return obj.get_name_display()
    get_display_name.short_description = 'Display Name'


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'user', 'category', 'purchase_value', 'current_value',
        'purchase_date', 'status', 'depreciation_percentage'
    ]
    list_filter = [
        'category', 'status', 'purchase_date', 'created_at'
    ]
    search_fields = ['name', 'vendor', 'serial_number', 'user__email']
    date_hierarchy = 'purchase_date'
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'depreciation_amount', 
        'depreciation_percentage'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'name', 'category')
        }),
        ('Valuation', {
            'fields': ('purchase_value', 'current_value', 'purchase_date')
        }),
        ('Status & Details', {
            'fields': ('status', 'disposal_date', 'vendor', 'serial_number', 'location')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Calculated Fields', {
            'fields': ('depreciation_amount', 'depreciation_percentage'),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'category')


@admin.register(IncomeRecord)
class IncomeRecordAdmin(admin.ModelAdmin):
    list_display = [
        'description', 'user', 'source', 'amount', 'income_date', 'created_at'
    ]
    list_filter = ['source', 'income_date', 'created_at']
    search_fields = ['description', 'user__email']
    date_hierarchy = 'income_date'
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Income Information', {
            'fields': ('user', 'source', 'amount', 'income_date', 'description')
        }),
        ('Reference Information', {
            'fields': ('sale_id', 'service_record_id')
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(TurnoverTaxRecord)
class TurnoverTaxRecordAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'year', 'month', 'total_revenue', 'taxable_amount',
        'tax_due', 'payment_status', 'is_eligible_for_turnover_tax'
    ]
    list_filter = ['year', 'month', 'payment_status', 'calculated_at']
    search_fields = ['user__email', 'payment_reference']
    readonly_fields = [
        'id', 'taxable_amount', 'tax_due', 'calculated_at', 'updated_at',
        'is_eligible_for_turnover_tax'
    ]
    
    fieldsets = (
        ('Tax Period', {
            'fields': ('user', 'year', 'month')
        }),
        ('Revenue & Calculation', {
            'fields': (
                'total_revenue', 'tax_free_threshold', 'taxable_amount',
                'tax_rate', 'tax_due'
            )
        }),
        ('Payment Information', {
            'fields': ('payment_status', 'payment_date', 'payment_reference')
        }),
        ('System Information', {
            'fields': ('id', 'calculated_at', 'updated_at', 'is_eligible_for_turnover_tax'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    def is_eligible_for_turnover_tax(self, obj):
        if obj.is_eligible_for_turnover_tax:
            return format_html('<span style="color: green;">Yes</span>')
        return format_html('<span style="color: red;">No</span>')
    is_eligible_for_turnover_tax.short_description = 'Eligible'


@admin.register(FinancialSummary)
class FinancialSummaryAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'year', 'month', 'total_income', 'total_expenses',
        'net_profit', 'total_assets', 'turnover_tax_due'
    ]
    list_filter = ['year', 'month', 'calculated_at']
    search_fields = ['user__email']
    readonly_fields = [
        'id', 'total_income', 'total_expenses', 'net_profit',
        'total_assets', 'turnover_tax_due', 'calculated_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Summary Period', {
            'fields': ('user', 'year', 'month')
        }),
        ('Financial Metrics', {
            'fields': (
                'total_income', 'total_expenses', 'net_profit',
                'total_assets', 'turnover_tax_due'
            )
        }),
        ('System Information', {
            'fields': ('id', 'calculated_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


# Admin site customization
admin.site.site_header = "Metrilabs Accounting Administration"
admin.site.site_title = "Accounting Admin"
admin.site.index_title = "Accounting Management"
