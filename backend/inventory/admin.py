from django.contrib import admin
from django import forms
from django.contrib.auth import get_user_model
from .models import Product, ProductCategory, Inventory, StockMovement, StockAlert


class InventoryInline(admin.StackedInline):
    """Inline inventory for product admin"""
    model = Inventory
    extra = 0
    readonly_fields = ('last_stock_update', 'created_at')


class StockMovementInline(admin.TabularInline):
    """Inline stock movements for product admin"""
    model = StockMovement
    extra = 0
    readonly_fields = ('quantity_before', 'quantity_after', 'created_by', 'created_at')
    ordering = ['-created_at']
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('get_name_display', 'description', 'is_active', 'product_count', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    def get_name_display(self, obj):
        return obj.get_name_display()
    get_name_display.short_description = 'Category Name'
    
    def product_count(self, obj):
        return obj.products.filter(is_active=True).count()
    product_count.short_description = 'Active Products'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'sku',
        'category_name',
        'selling_price',
        'cost_price',
        'current_stock',
        'stock_status',
        'is_active',
        'user_email'
    )
    list_filter = (
        'is_active',
        'category',
        'unit_of_measure',
        'user',  # Added user filter
        'created_at'
    )
    search_fields = (
        'name',
        'sku',
        'description',
        'user__email'
    )
    readonly_fields = ('current_stock', 'stock_value', 'selling_value', 'profit_margin', 'created_at', 'updated_at')
    inlines = [InventoryInline, StockMovementInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'name', 'sku', 'description', 'category')
        }),
        ('Pricing', {
            'fields': ('selling_price', 'cost_price', 'unit_of_measure')
        }),
        ('Stock Information', {
            'fields': ('current_stock', 'stock_value', 'selling_value', 'profit_margin'),
            'classes': ('collapse',)
        }),
        ('Status & Dates', {
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        """Filter products by user for non-superusers"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Limit user selection to current user for non-superusers"""
        if db_field.name == "user" and not request.user.is_superuser:
            kwargs["queryset"] = get_user_model().objects.filter(id=request.user.id)
            kwargs["initial"] = request.user.id
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def save_model(self, request, obj, form, change):
        """Set user to current user if not set"""
        if not change and not request.user.is_superuser:  # Only for new objects and non-superusers
            obj.user = request.user
        super().save_model(request, obj, form, change)
    
    def category_name(self, obj):
        return obj.category.get_name_display() if obj.category else 'Uncategorized'
    category_name.short_description = 'Category'
    
    def current_stock(self, obj):
        return f"{obj.current_stock} {obj.get_unit_of_measure_display()}"
    current_stock.short_description = 'Current Stock'
    
    def stock_status(self, obj):
        if hasattr(obj, 'inventory'):
            return obj.inventory.stock_status
        return 'No Inventory'
    stock_status.short_description = 'Stock Status'
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Owner'


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = (
        'product_name',
        'quantity_in_stock',
        'reorder_level',
        'stock_status',
        'is_low_stock',
        'user_email',
        'last_stock_update'
    )
    list_filter = (
        'product__user',  # Added user filter
        'last_stock_update',
        'created_at'
    )
    search_fields = (
        'product__name',
        'product__sku',
        'product__user__email'
    )
    readonly_fields = ('stock_status', 'is_low_stock', 'last_stock_update', 'created_at')
    
    def get_queryset(self, request):
        """Filter inventory by user for non-superusers"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(product__user=request.user)
    
    def product_name(self, obj):
        return obj.product.name
    product_name.short_description = 'Product'
    
    def user_email(self, obj):
        return obj.product.user.email
    user_email.short_description = 'Owner'
    
    def has_add_permission(self, request):
        # Inventory should be created automatically with products
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of inventory records
        return False


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = (
        'product_name',
        'movement_type',
        'quantity',
        'quantity_after',
        'created_by_name',
        'user_email',
        'created_at'
    )
    list_filter = (
        'movement_type',
        'product__user',  # Added user filter
        'created_at',
        'product__category'
    )
    search_fields = (
        'product__name',
        'product__sku',
        'reference_number',
        'notes',
        'created_by__email',
        'product__user__email'
    )
    readonly_fields = (
        'quantity_before',
        'quantity_after',
        'is_inbound',
        'is_outbound',
        'created_by',
        'created_at'
    )
    
    fieldsets = (
        ('Movement Information', {
            'fields': (
                'product',
                'movement_type',
                'quantity',
                'quantity_before',
                'quantity_after'
            )
        }),
        ('Details', {
            'fields': ('reference_number', 'notes')
        }),
        ('Metadata', {
            'fields': ('is_inbound', 'is_outbound', 'created_by', 'created_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        """Filter stock movements by user for non-superusers"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(product__user=request.user)
    
    def product_name(self, obj):
        return obj.product.name
    product_name.short_description = 'Product'
    
    def created_by_name(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else 'System'
    created_by_name.short_description = 'Created By'
    
    def user_email(self, obj):
        return obj.product.user.email
    user_email.short_description = 'Product Owner'
    
    def has_add_permission(self, request):
        # Stock movements should be created through the API
        return False
    
    def has_change_permission(self, request, obj=None):
        # Don't allow editing of stock movements
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of stock movements
        return False


@admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    list_display = (
        'product_name',
        'alert_type',
        'current_stock',
        'reorder_level',
        'is_resolved',
        'user_email',
        'created_at'
    )
    list_filter = (
        'alert_type',
        'is_resolved',
        'product__user',  # Added user filter
        'created_at',
        'product__category'
    )
    search_fields = (
        'product__name',
        'product__sku',
        'product__user__email'
    )
    readonly_fields = ('created_at', 'resolved_at')
    
    def get_queryset(self, request):
        """Filter stock alerts by user for non-superusers"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(product__user=request.user)
    
    def product_name(self, obj):
        return obj.product.name
    product_name.short_description = 'Product'
    
    def user_email(self, obj):
        return obj.product.user.email
    user_email.short_description = 'Product Owner'
    
    actions = ['mark_resolved']
    
    def mark_resolved(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(is_resolved=False).update(
            is_resolved=True,
            resolved_at=timezone.now()
        )
        self.message_user(request, f'{updated} alerts marked as resolved.')
    mark_resolved.short_description = 'Mark selected alerts as resolved'
