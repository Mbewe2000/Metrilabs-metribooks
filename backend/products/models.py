from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class ProductCategory(models.Model):
    """Product categories for organizing products"""
    name = models.CharField(max_length=100, unique=True, help_text="Category name (e.g., Beverages, Electronics)")
    description = models.TextField(blank=True, help_text="Optional description of the category")
    is_active = models.BooleanField(default=True, help_text="Whether this category is active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_categories'
    )

    class Meta:
        verbose_name = "Product Category"
        verbose_name_plural = "Product Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def active_products_count(self):
        """Count of active products in this category"""
        return self.products.filter(is_active=True).count()


class Product(models.Model):
    """Product model with all required fields"""
    
    UNIT_CHOICES = [
        ('each', 'Each'),
        ('kg', 'Kilogram'),
        ('g', 'Gram'),
        ('liter', 'Liter'),
        ('ml', 'Milliliter'),
        ('meter', 'Meter'),
        ('cm', 'Centimeter'),
        ('pack', 'Pack'),
        ('box', 'Box'),
        ('dozen', 'Dozen'),
        ('pair', 'Pair'),
        ('set', 'Set'),
        ('bottle', 'Bottle'),
        ('can', 'Can'),
        ('bag', 'Bag'),
    ]

    # Basic product information
    name = models.CharField(max_length=255, help_text="Product name")
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.PROTECT,
        related_name='products',
        help_text="Product category"
    )
    description = models.TextField(blank=True, help_text="Optional product description")
    
    # Pricing (in Zambian Kwacha)
    selling_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Selling price in ZMW"
    )
    cost_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        blank=True,
        null=True,
        help_text="Optional cost price in ZMW"
    )
    
    # Product details
    unit_of_measure = models.CharField(
        max_length=20,
        choices=UNIT_CHOICES,
        default='each',
        help_text="Unit of measure for this product"
    )
    sku = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True,
        help_text="Optional SKU or Product Code"
    )
    
    # Status and metadata
    is_active = models.BooleanField(default=True, help_text="Whether this product is active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_products'
    )

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ['name']
        unique_together = ['name', 'category']  # Prevent duplicate product names in same category

    def __str__(self):
        return f"{self.name} ({self.category.name})"

    def save(self, *args, **kwargs):
        # Auto-generate SKU if not provided
        if not self.sku:
            # Generate SKU based on category and product name
            category_prefix = self.category.name[:3].upper()
            name_prefix = ''.join([word[:2].upper() for word in self.name.split()[:2]])
            unique_suffix = str(uuid.uuid4())[:8].upper()
            self.sku = f"{category_prefix}-{name_prefix}-{unique_suffix}"
        super().save(*args, **kwargs)

    @property
    def profit_margin(self):
        """Calculate profit margin if cost price is available"""
        if self.cost_price and self.cost_price > 0:
            return ((self.selling_price - self.cost_price) / self.cost_price) * 100
        return None

    @property
    def profit_amount(self):
        """Calculate profit amount if cost price is available"""
        if self.cost_price:
            return self.selling_price - self.cost_price
        return None

    @property
    def current_stock(self):
        """Get current stock level"""
        inventory = getattr(self, 'inventory', None)
        return inventory.quantity_in_stock if inventory else 0

    @property
    def stock_value(self):
        """Calculate total stock value based on cost price"""
        if self.cost_price:
            return self.current_stock * self.cost_price
        return None

    @property
    def is_low_stock(self):
        """Check if product is low on stock"""
        inventory = getattr(self, 'inventory', None)
        if inventory and inventory.reorder_level:
            return self.current_stock <= inventory.reorder_level
        return False


class ProductInventory(models.Model):
    """Inventory tracking for each product"""
    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name='inventory',
        help_text="Product for this inventory record"
    )
    quantity_in_stock = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=Decimal('0.000'),
        validators=[MinValueValidator(Decimal('0.000'))],
        help_text="Current quantity in stock"
    )
    reorder_level = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0.000'))],
        help_text="Optional reorder level for low stock alerts"
    )
    last_restocked = models.DateTimeField(blank=True, null=True, help_text="Last restock date")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Product Inventory"
        verbose_name_plural = "Product Inventories"

    def __str__(self):
        return f"{self.product.name} - Stock: {self.quantity_in_stock} {self.product.unit_of_measure}"

    @property
    def is_low_stock(self):
        """Check if this inventory is low on stock"""
        if self.reorder_level:
            return self.quantity_in_stock <= self.reorder_level
        return False

    @property
    def stock_value_cost(self):
        """Calculate stock value based on cost price"""
        if self.product.cost_price:
            return self.quantity_in_stock * self.product.cost_price
        return None

    @property
    def stock_value_selling(self):
        """Calculate stock value based on selling price"""
        return self.quantity_in_stock * self.product.selling_price


class StockMovement(models.Model):
    """Track all stock movements for audit trail"""
    
    MOVEMENT_TYPES = [
        ('manual_in', 'Manual Stock In'),
        ('manual_out', 'Manual Stock Out'),
        ('opening_stock', 'Opening Stock'),
        ('restock', 'Restock'),
        ('adjustment', 'Stock Adjustment'),
        ('damage', 'Damaged/Expired'),
        ('theft', 'Theft/Loss'),
        ('sale', 'Sale (Auto)'),  # For future sales integration
        ('return', 'Return'),
        ('transfer', 'Transfer'),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='stock_movements',
        help_text="Product for this stock movement"
    )
    movement_type = models.CharField(
        max_length=20,
        choices=MOVEMENT_TYPES,
        help_text="Type of stock movement"
    )
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        help_text="Quantity moved (positive for in, negative for out)"
    )
    quantity_before = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        help_text="Quantity before this movement"
    )
    quantity_after = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        help_text="Quantity after this movement"
    )
    reference_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Optional reference number (invoice, receipt, etc.)"
    )
    notes = models.TextField(blank=True, help_text="Optional notes about this movement")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='stock_movements'
    )

    class Meta:
        verbose_name = "Stock Movement"
        verbose_name_plural = "Stock Movements"
        ordering = ['-created_at']

    def __str__(self):
        direction = "IN" if self.quantity >= 0 else "OUT"
        return f"{self.product.name} - {direction} {abs(self.quantity)} {self.product.unit_of_measure}"

    def save(self, *args, **kwargs):
        # Auto-generate reference number if not provided
        if not self.reference_number:
            import datetime
            date_str = datetime.datetime.now().strftime("%Y%m%d")
            movement_count = StockMovement.objects.filter(
                created_at__date=datetime.datetime.now().date()
            ).count() + 1
            self.reference_number = f"MOV-{date_str}-{movement_count:04d}"
        
        super().save(*args, **kwargs)
