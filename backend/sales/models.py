from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.utils import timezone
import uuid

User = get_user_model()


class Sale(models.Model):
    """Main sales record"""
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('mobile_money', 'Mobile Money'),
        ('bank_transfer', 'Bank Transfer'),
        ('card', 'Card Payment'),
        ('credit', 'Credit/Account'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('completed', 'Completed'),
        ('pending', 'Pending'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sales')
    sale_number = models.CharField(max_length=50, help_text="Auto-generated sale number")
    
    # Sale details
    sale_date = models.DateTimeField(default=timezone.now, help_text="Date and time of sale")
    customer_name = models.CharField(max_length=200, blank=True, help_text="Customer name (optional)")
    customer_phone = models.CharField(max_length=20, blank=True, help_text="Customer phone (optional)")
    customer_email = models.EmailField(blank=True, help_text="Customer email (optional)")
    
    # Financial details
    subtotal = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Total before discount and tax"
    )
    discount_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Total discount applied"
    )
    tax_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Tax amount"
    )
    total_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Final total amount"
    )
    
    # Payment details
    payment_method = models.CharField(
        max_length=20, 
        choices=PAYMENT_METHOD_CHOICES,
        default='cash',
        help_text="Payment method used"
    )
    payment_reference = models.CharField(
        max_length=100, 
        blank=True,
        help_text="Payment reference number (e.g., mobile money transaction ID)"
    )
    amount_paid = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Amount actually paid"
    )
    change_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Change given to customer"
    )
    
    # Status and metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    notes = models.TextField(blank=True, help_text="Additional notes about the sale")
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-sale_date']
        unique_together = ['user', 'sale_number']
    
    def __str__(self):
        return f"Sale {self.sale_number} - ZMW {self.total_amount}"
    
    def save(self, *args, **kwargs):
        if not self.sale_number:
            self.sale_number = self.generate_sale_number()
        super().save(*args, **kwargs)
    
    def generate_sale_number(self):
        """Generate unique sale number"""
        from datetime import datetime
        today = datetime.now()
        prefix = f"SL{today.strftime('%Y%m%d')}"
        
        # Get last sale number for today
        last_sale = Sale.objects.filter(
            user=self.user,
            sale_number__startswith=prefix
        ).order_by('-sale_number').first()
        
        if last_sale:
            # Extract sequence number and increment
            try:
                last_seq = int(last_sale.sale_number[-4:])
                new_seq = last_seq + 1
            except (ValueError, IndexError):
                new_seq = 1
        else:
            new_seq = 1
        
        return f"{prefix}{new_seq:04d}"
    
    @property
    def balance_due(self):
        """Calculate remaining balance"""
        return self.total_amount - self.amount_paid
    
    @property
    def is_fully_paid(self):
        """Check if sale is fully paid"""
        return self.amount_paid >= self.total_amount


class SaleItem(models.Model):
    """Individual items in a sale"""
    ITEM_TYPE_CHOICES = [
        ('product', 'Product'),
        ('service', 'Service'),
    ]
    
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    item_type = models.CharField(max_length=10, choices=ITEM_TYPE_CHOICES)
    
    # Foreign keys to different item types
    product = models.ForeignKey(
        'inventory.Product', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        help_text="Product sold (if item_type=product)"
    )
    service = models.ForeignKey(
        'services.Service', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        help_text="Service sold (if item_type=service)"
    )
    
    # Item details
    item_name = models.CharField(max_length=200, help_text="Name of item at time of sale")
    quantity = models.DecimalField(
        max_digits=10, 
        decimal_places=3,
        validators=[MinValueValidator(Decimal('0.001'))],
        help_text="Quantity sold"
    )
    unit_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Price per unit at time of sale"
    )
    discount_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Discount applied to this item"
    )
    total_price = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Total price for this line item"
    )
    
    # Metadata
    notes = models.TextField(blank=True, help_text="Notes about this item")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['id']
    
    def __str__(self):
        return f"{self.item_name} x {self.quantity} @ ZMW {self.unit_price}"
    
    def save(self, *args, **kwargs):
        # Calculate total price
        line_total = (self.quantity * self.unit_price) - self.discount_amount
        self.total_price = max(line_total, Decimal('0.00'))
        
        # Set item name from related object if not provided
        if not self.item_name:
            if self.item_type == 'product' and self.product:
                self.item_name = self.product.name
            elif self.item_type == 'service' and self.service:
                self.item_name = self.service.name
        
        super().save(*args, **kwargs)
    
    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Ensure only one item type is selected
        if self.item_type == 'product' and not self.product:
            raise ValidationError("Product must be selected when item_type is 'product'")
        if self.item_type == 'service' and not self.service:
            raise ValidationError("Service must be selected when item_type is 'service'")
        
        # Ensure mutually exclusive selection
        if self.product and self.service:
            raise ValidationError("Cannot select both product and service for the same item")


class SalesReport(models.Model):
    """Pre-calculated sales reports for performance"""
    REPORT_TYPE_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sales_reports')
    report_type = models.CharField(max_length=10, choices=REPORT_TYPE_CHOICES)
    period_start = models.DateField(help_text="Start date of reporting period")
    period_end = models.DateField(help_text="End date of reporting period")
    
    # Summary metrics
    total_sales = models.IntegerField(default=0, help_text="Number of sales")
    total_revenue = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Total revenue"
    )
    total_discounts = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Total discounts given"
    )
    total_tax = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Total tax collected"
    )
    
    # Payment method breakdown (stored as JSON)
    payment_method_breakdown = models.JSONField(
        default=dict,
        help_text="Breakdown of sales by payment method"
    )
    
    # Top products/services (stored as JSON)
    top_products = models.JSONField(
        default=list,
        help_text="Top selling products for the period"
    )
    top_services = models.JSONField(
        default=list,
        help_text="Top selling services for the period"
    )
    
    # Metadata
    generated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-period_end']
        unique_together = ['user', 'report_type', 'period_start', 'period_end']
    
    def __str__(self):
        return f"{self.report_type.title()} Report: {self.period_start} to {self.period_end}"
