from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import ProductCategory, Product, ProductInventory, StockMovement


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'active_products_count', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('active_products_count', 'created_at', 'updated_at', 'created_by')
    fieldsets = (
        ('Category Information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Metadata', {
            'fields': ('active_products_count', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    ordering = ('name',)

    def save_model(self, request, obj, form, change):
        if not change:  # Creating new category
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class ProductInventoryInline(admin.StackedInline):
    model = ProductInventory
    extra = 0
    readonly_fields = ('is_low_stock', 'stock_value_cost', 'stock_value_selling', 'created_at', 'updated_at')
    fieldsets = (
        ('Stock Information', {
            'fields': ('quantity_in_stock', 'reorder_level', 'last_restocked')
        }),
        ('Calculated Values', {
            'fields': ('is_low_stock', 'stock_value_cost', 'stock_value_selling'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name', 
        'category', 
        'sku', 
        'selling_price_zmw', 
        'current_stock_display', 
        'stock_status',
        'is_active'
    )
    list_filter = ('category', 'is_active', 'unit_of_measure', 'created_at')
    search_fields = ('name', 'sku', 'description', 'category__name')
    readonly_fields = (
        'sku', 
        'profit_margin', 
        'profit_amount', 
        'current_stock', 
        'stock_value',
        'is_low_stock',
        'created_at', 
        'updated_at', 
        'created_by'
    )
    inlines = [ProductInventoryInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category', 'description', 'is_active')
        }),
        ('Pricing (ZMW)', {
            'fields': ('selling_price', 'cost_price', 'profit_margin', 'profit_amount')
        }),
        ('Product Details', {
            'fields': ('unit_of_measure', 'sku')
        }),
        ('Stock Information', {
            'fields': ('current_stock', 'stock_value', 'is_low_stock'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    ordering = ('name',)

    def save_model(self, request, obj, form, change):
        if not change:  # Creating new product
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def selling_price_zmw(self, obj):
        return f"ZMW {obj.selling_price:,.2f}"
    selling_price_zmw.short_description = 'Selling Price'
    selling_price_zmw.admin_order_field = 'selling_price'

    def current_stock_display(self, obj):
        stock = obj.current_stock
        return f"{stock} {obj.unit_of_measure}"
    current_stock_display.short_description = 'Current Stock'

    def stock_status(self, obj):
        if obj.is_low_stock:
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠️ LOW STOCK</span>'
            )
        elif obj.current_stock == 0:
            return format_html(
                '<span style="color: darkred; font-weight: bold;">❌ OUT OF STOCK</span>'
            )
        else:
            return format_html(
                '<span style="color: green; font-weight: bold;">✅ IN STOCK</span>'
            )
    stock_status.short_description = 'Stock Status'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category', 'inventory')


@admin.register(ProductInventory)
class ProductInventoryAdmin(admin.ModelAdmin):
    list_display = (
        'product_name',
        'category_name',
        'quantity_display',
        'reorder_level_display',
        'stock_status',
        'stock_value_display',
        'last_restocked'
    )
    list_filter = ('product__category', 'product__unit_of_measure', 'last_restocked')
    search_fields = ('product__name', 'product__sku', 'product__category__name')
    readonly_fields = (
        'product',
        'is_low_stock',
        'stock_value_cost',
        'stock_value_selling',
        'created_at',
        'updated_at'
    )
    fieldsets = (
        ('Product Information', {
            'fields': ('product',)
        }),
        ('Stock Levels', {
            'fields': ('quantity_in_stock', 'reorder_level', 'last_restocked')
        }),
        ('Calculated Values', {
            'fields': ('is_low_stock', 'stock_value_cost', 'stock_value_selling'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def product_name(self, obj):
        return obj.product.name
    product_name.short_description = 'Product'
    product_name.admin_order_field = 'product__name'

    def category_name(self, obj):
        return obj.product.category.name
    category_name.short_description = 'Category'
    category_name.admin_order_field = 'product__category__name'

    def quantity_display(self, obj):
        return f"{obj.quantity_in_stock} {obj.product.unit_of_measure}"
    quantity_display.short_description = 'Quantity in Stock'

    def reorder_level_display(self, obj):
        if obj.reorder_level:
            return f"{obj.reorder_level} {obj.product.unit_of_measure}"
        return "Not set"
    reorder_level_display.short_description = 'Reorder Level'

    def stock_status(self, obj):
        if obj.is_low_stock:
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠️ LOW</span>'
            )
        elif obj.quantity_in_stock == 0:
            return format_html(
                '<span style="color: darkred; font-weight: bold;">❌ OUT</span>'
            )
        else:
            return format_html(
                '<span style="color: green; font-weight: bold;">✅ OK</span>'
            )
    stock_status.short_description = 'Status'

    def stock_value_display(self, obj):
        if obj.stock_value_cost:
            return f"ZMW {obj.stock_value_cost:,.2f}"
        return "N/A"
    stock_value_display.short_description = 'Stock Value (Cost)'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product__category')

    def has_add_permission(self, request):
        # Inventory records are created automatically with products
        return False


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = (
        'reference_number',
        'product_name',
        'movement_type',
        'quantity_display',
        'movement_direction',
        'created_at',
        'created_by_display'
    )
    list_filter = ('movement_type', 'created_at', 'product__category')
    search_fields = (
        'product__name', 
        'product__sku', 
        'reference_number', 
        'notes',
        'created_by__email'
    )
    readonly_fields = (
        'product',
        'quantity_before',
        'quantity_after',
        'reference_number',
        'created_at',
        'created_by'
    )
    fieldsets = (
        ('Movement Information', {
            'fields': ('product', 'movement_type', 'quantity', 'reference_number')
        }),
        ('Stock Levels', {
            'fields': ('quantity_before', 'quantity_after')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        })
    )
    ordering = ('-created_at',)

    def product_name(self, obj):
        return obj.product.name
    product_name.short_description = 'Product'
    product_name.admin_order_field = 'product__name'

    def quantity_display(self, obj):
        return f"{abs(obj.quantity)} {obj.product.unit_of_measure}"
    quantity_display.short_description = 'Quantity'

    def movement_direction(self, obj):
        if obj.quantity > 0:
            return format_html(
                '<span style="color: green; font-weight: bold;">📈 IN</span>'
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">📉 OUT</span>'
            )
    movement_direction.short_description = 'Direction'

    def created_by_display(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.email
        return "System"
    created_by_display.short_description = 'Created By'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product', 'created_by')

    def has_add_permission(self, request):
        # Stock movements should be created through the API for proper validation
        return False

    def has_change_permission(self, request, obj=None):
        # Stock movements should not be edited once created
        return False

    def has_delete_permission(self, request, obj=None):
        # Only superusers can delete stock movements
        return request.user.is_superuser
