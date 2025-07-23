from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class ProductCategory(models.Model):
    """Product categories for organizing inventory items"""
    
    # Predefined categories for products (not services)
    CATEGORY_CHOICES = [
        ('food_beverage', 'Food & Beverage'),
        ('electronics', 'Electronics'),
        ('clothing_accessories', 'Clothing & Accessories'),
        ('health_beauty', 'Health & Beauty'),
        ('home_garden', 'Home & Garden'),
        ('books_stationery', 'Books & Stationery'),
        ('sports_outdoor', 'Sports & Outdoor'),
        ('automotive', 'Automotive'),
        ('toys_games', 'Toys & Games'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        unique=True,
        help_text="Product category"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Category description"
    )
    is_active = models.BooleanField(default=True, help_text="Whether category is active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Product Category"
        verbose_name_plural = "Product Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.get_name_display()


class Product(models.Model):
    """Product model for inventory management"""
    
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
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='products',
        help_text="Product owner"
    )
    name = models.CharField(max_length=255, help_text="Product name")
    sku = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Stock Keeping Unit or Product Code"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Product description"
    )
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        help_text="Product category"
    )
    
    # Pricing
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
        help_text="Cost price in ZMW (optional)"
    )
    
    # Unit and measurement
    unit_of_measure = models.CharField(
        max_length=20,
        choices=UNIT_CHOICES,
        default='each',
        help_text="Unit of measurement"
    )
    
    # Status and metadata
    is_active = models.BooleanField(default=True, help_text="Whether product is active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ['name']
        unique_together = ['user', 'sku']  # SKU unique per user
    
    def __str__(self):
        return f"{self.name} ({self.get_unit_of_measure_display()})"
    
    @property
    def profit_margin(self):
        """Calculate profit margin if cost price is available"""
        if self.cost_price and self.cost_price > 0:
            return ((self.selling_price - self.cost_price) / self.cost_price) * 100
        return None
    
    @property
    def current_stock(self):
        """Get current stock quantity"""
        if hasattr(self, 'inventory'):
            return self.inventory.quantity_in_stock
        return 0
    
    @property
    def stock_value(self):
        """Calculate total stock value based on cost price"""
        if self.cost_price:
            return self.current_stock * self.cost_price
        return None
    
    @property
    def selling_value(self):
        """Calculate total stock value based on selling price"""
        return self.current_stock * self.selling_price


class Inventory(models.Model):
    """Inventory tracking for products"""
    
    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name='inventory',
        help_text="Related product"
    )
    quantity_in_stock = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(Decimal('0.000'))],
        help_text="Current quantity in stock"
    )
    reorder_level = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0.000'))],
        help_text="Minimum stock level before reorder alert"
    )
    opening_stock = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(Decimal('0.000'))],
        help_text="Initial stock quantity"
    )
    last_stock_update = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Inventory"
        verbose_name_plural = "Inventories"
    
    def __str__(self):
        return f"{self.product.name} - Stock: {self.quantity_in_stock} {self.product.get_unit_of_measure_display()}"
    
    @property
    def is_low_stock(self):
        """Check if stock is below reorder level"""
        if self.reorder_level:
            return self.quantity_in_stock <= self.reorder_level
        return False
    
    @property
    def stock_status(self):
        """Get stock status description"""
        if self.quantity_in_stock <= 0:
            return "Out of Stock"
        elif self.is_low_stock:
            return "Low Stock"
        else:
            return "In Stock"


class StockMovement(models.Model):
    """Track all stock movements for audit trail"""
    
    MOVEMENT_TYPE_CHOICES = [
        ('opening_stock', 'Opening Stock'),
        ('stock_in', 'Stock In (Manual)'),
        ('stock_out', 'Stock Out (Manual)'),
        ('sale', 'Sale (Auto)'),
        ('return', 'Return'),
        ('adjustment', 'Stock Adjustment'),
        ('damage', 'Damaged/Expired'),
        ('theft', 'Theft/Loss'),
    ]
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='stock_movements',
        help_text="Related product"
    )
    movement_type = models.CharField(
        max_length=20,
        choices=MOVEMENT_TYPE_CHOICES,
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
        help_text="Stock quantity before this movement"
    )
    quantity_after = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        help_text="Stock quantity after this movement"
    )
    reference_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Reference number (e.g., invoice, receipt)"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes about the movement"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='stock_movements',
        help_text="User who performed the movement"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Stock Movement"
        verbose_name_plural = "Stock Movements"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.product.name} - {self.get_movement_type_display()} - {self.quantity}"
    
    @property
    def is_inbound(self):
        """Check if this is an inbound movement"""
        return self.quantity > 0
    
    @property
    def is_outbound(self):
        """Check if this is an outbound movement"""
        return self.quantity < 0


class StockAlert(models.Model):
    """Stock alerts for low inventory levels"""
    
    ALERT_TYPE_CHOICES = [
        ('low_stock', 'Low Stock'),
        ('out_of_stock', 'Out of Stock'),
    ]
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='stock_alerts',
        help_text="Product with alert"
    )
    alert_type = models.CharField(
        max_length=20,
        choices=ALERT_TYPE_CHOICES,
        help_text="Type of alert"
    )
    current_stock = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        help_text="Stock level when alert was created"
    )
    reorder_level = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        blank=True,
        null=True,
        help_text="Reorder level at time of alert"
    )
    is_resolved = models.BooleanField(default=False, help_text="Whether alert is resolved")
    resolved_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Stock Alert"
        verbose_name_plural = "Stock Alerts"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.product.name} - {self.get_alert_type_display()}"
