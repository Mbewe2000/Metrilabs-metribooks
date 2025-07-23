from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid

User = settings.AUTH_USER_MODEL


class ExpenseCategory(models.Model):
    """Categories for organizing expenses"""
    
    CATEGORY_CHOICES = [
        ('operational', 'Operational'),
        ('staff', 'Staff & Salaries'),
        ('utilities', 'Utilities'),
        ('transport', 'Transport'),
        ('marketing', 'Marketing & Advertising'),
        ('equipment', 'Equipment & Tools'),
        ('professional', 'Professional Services'),
        ('rent', 'Rent & Facilities'),
        ('insurance', 'Insurance'),
        ('loan_payments', 'Loan Payments'),
        ('taxes', 'Taxes & Fees'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=50, choices=CATEGORY_CHOICES, unique=True)
    description = models.TextField(blank=True, help_text="Category description")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Expense Categories"
        ordering = ['name']
    
    def __str__(self):
        return dict(self.CATEGORY_CHOICES)[self.name]


class Expense(models.Model):
    """Track business expenses and liabilities"""
    
    PAYMENT_STATUS_CHOICES = [
        ('paid', 'Paid'),
        ('unpaid', 'Unpaid'),
        ('overdue', 'Overdue'),
        ('partial', 'Partially Paid'),
    ]
    
    EXPENSE_TYPE_CHOICES = [
        ('one_time', 'One-time Expense'),
        ('recurring', 'Recurring Expense'),
    ]
    
    RECURRENCE_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually'),
    ]
    
    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses')
    
    # Expense details
    name = models.CharField(max_length=200, help_text="Expense description")
    category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT)
    amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Expense amount in Kwacha"
    )
    
    # Type and recurrence
    expense_type = models.CharField(max_length=20, choices=EXPENSE_TYPE_CHOICES, default='one_time')
    recurrence = models.CharField(
        max_length=20, 
        choices=RECURRENCE_CHOICES, 
        blank=True, 
        null=True,
        help_text="For recurring expenses only"
    )
    
    # Dates and payment
    expense_date = models.DateField(default=timezone.now, help_text="Date expense was incurred")
    due_date = models.DateField(blank=True, null=True, help_text="Payment due date")
    payment_date = models.DateField(blank=True, null=True, help_text="Date payment was made")
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    
    # Additional details
    vendor = models.CharField(max_length=200, blank=True, help_text="Vendor/supplier name")
    reference_number = models.CharField(max_length=100, blank=True, help_text="Invoice/receipt number")
    notes = models.TextField(blank=True, help_text="Additional notes")
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-expense_date', '-created_at']
        indexes = [
            models.Index(fields=['user', 'expense_date']),
            models.Index(fields=['user', 'category']),
            models.Index(fields=['user', 'payment_status']),
        ]
    
    def __str__(self):
        return f"{self.name} - K{self.amount} ({self.expense_date})"
    
    @property
    def is_overdue(self):
        """Check if unpaid expense is overdue"""
        if self.payment_status in ['paid', 'partial'] or not self.due_date:
            return False
        return self.due_date < timezone.now().date()
    
    def save(self, *args, **kwargs):
        """Update payment status based on due date"""
        if self.payment_status == 'unpaid' and self.is_overdue:
            self.payment_status = 'overdue'
        super().save(*args, **kwargs)


class AssetCategory(models.Model):
    """Categories for organizing business assets"""
    
    CATEGORY_CHOICES = [
        ('fixed_assets', 'Fixed Assets'),
        ('current_assets', 'Current Assets'),
        ('intangible_assets', 'Intangible Assets'),
        ('equipment', 'Equipment & Machinery'),
        ('vehicles', 'Vehicles'),
        ('furniture', 'Furniture & Fixtures'),
        ('buildings', 'Buildings & Property'),
        ('technology', 'Technology & Software'),
        ('other', 'Other Assets'),
    ]
    
    name = models.CharField(max_length=50, choices=CATEGORY_CHOICES, unique=True)
    description = models.TextField(blank=True, help_text="Category description")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Asset Categories"
        ordering = ['name']
    
    def __str__(self):
        return dict(self.CATEGORY_CHOICES)[self.name]


class Asset(models.Model):
    """Track business assets and their valuation"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('disposed', 'Disposed'),
        ('damaged', 'Damaged'),
        ('under_repair', 'Under Repair'),
    ]
    
    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assets')
    
    # Asset details
    name = models.CharField(max_length=200, help_text="Asset name/description")
    category = models.ForeignKey(AssetCategory, on_delete=models.PROTECT)
    
    # Valuation
    purchase_value = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Original purchase price in Kwacha"
    )
    current_value = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Current estimated value in Kwacha",
        blank=True,
        null=True
    )
    
    # Dates and status
    purchase_date = models.DateField(help_text="Date asset was purchased")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    disposal_date = models.DateField(blank=True, null=True, help_text="Date asset was disposed")
    
    # Additional details
    vendor = models.CharField(max_length=200, blank=True, help_text="Vendor/supplier name")
    serial_number = models.CharField(max_length=100, blank=True, help_text="Serial/model number")
    location = models.CharField(max_length=200, blank=True, help_text="Asset location")
    notes = models.TextField(blank=True, help_text="Additional notes")
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-purchase_date', 'name']
        indexes = [
            models.Index(fields=['user', 'category']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', 'purchase_date']),
        ]
    
    def __str__(self):
        return f"{self.name} - K{self.purchase_value} ({self.purchase_date})"
    
    @property
    def depreciation_amount(self):
        """Calculate depreciation amount"""
        if self.current_value is not None:
            return self.purchase_value - self.current_value
        return Decimal('0.00')
    
    @property
    def depreciation_percentage(self):
        """Calculate depreciation percentage"""
        if self.current_value is not None and self.purchase_value > 0:
            return ((self.purchase_value - self.current_value) / self.purchase_value) * 100
        return Decimal('0.00')


class IncomeRecord(models.Model):
    """Track income from various sources"""
    
    INCOME_SOURCE_CHOICES = [
        ('sales', 'Sales Revenue'),
        ('services', 'Service Income'),
        ('other', 'Other Income'),
    ]
    
    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='income_records')
    
    # Income details
    source = models.CharField(max_length=20, choices=INCOME_SOURCE_CHOICES)
    amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Income amount in Kwacha"
    )
    income_date = models.DateField(help_text="Date income was earned")
    description = models.CharField(max_length=200, help_text="Income description")
    
    # Reference to source record
    sale_id = models.UUIDField(blank=True, null=True, help_text="Reference to sale record")
    service_record_id = models.UUIDField(blank=True, null=True, help_text="Reference to service record")
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-income_date', '-created_at']
        indexes = [
            models.Index(fields=['user', 'income_date']),
            models.Index(fields=['user', 'source']),
        ]
    
    def __str__(self):
        return f"{self.description} - K{self.amount} ({self.income_date})"


class TurnoverTaxRecord(models.Model):
    """Track monthly turnover tax calculations"""
    
    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tax_records')
    
    # Tax period
    year = models.IntegerField(help_text="Tax year")
    month = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text="Tax month (1-12)"
    )
    
    # Revenue calculations
    total_revenue = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total monthly revenue in Kwacha"
    )
    tax_free_threshold = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        default=Decimal('1000.00'),
        help_text="Monthly tax-free threshold (K1,000)"
    )
    taxable_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Amount subject to tax"
    )
    tax_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        default=Decimal('5.00'),
        help_text="Tax rate percentage"
    )
    tax_due = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total turnover tax due"
    )
    
    # Payment tracking
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('paid', 'Paid'),
            ('overdue', 'Overdue'),
        ],
        default='pending'
    )
    payment_date = models.DateField(blank=True, null=True)
    payment_reference = models.CharField(max_length=100, blank=True, help_text="ZRA payment reference")
    
    # Tracking
    calculated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-year', '-month']
        unique_together = ['user', 'year', 'month']
        indexes = [
            models.Index(fields=['user', 'year', 'month']),
            models.Index(fields=['user', 'payment_status']),
        ]
    
    def __str__(self):
        return f"Turnover Tax {self.year}-{self.month:02d} - K{self.tax_due}"
    
    def calculate_tax(self):
        """Calculate turnover tax based on ZRA 2025 rules"""
        if self.total_revenue <= self.tax_free_threshold:
            self.taxable_amount = Decimal('0.00')
            self.tax_due = Decimal('0.00')
        else:
            self.taxable_amount = self.total_revenue - self.tax_free_threshold
            self.tax_due = (self.taxable_amount * self.tax_rate) / Decimal('100.00')
        
        self.save()
        return self.tax_due
    
    @classmethod
    def get_annual_turnover(cls, user, year):
        """Calculate total annual turnover for threshold checking"""
        annual_total = cls.objects.filter(
            user=user,
            year=year
        ).aggregate(
            total=models.Sum('total_revenue')
        )['total'] or Decimal('0.00')
        
        return annual_total
    
    @property
    def is_eligible_for_turnover_tax(self):
        """Check if business is eligible for turnover tax"""
        annual_turnover = self.get_annual_turnover(self.user, self.year)
        return annual_turnover <= Decimal('5000000.00')  # K5,000,000 threshold


class FinancialSummary(models.Model):
    """Monthly financial summary for quick reporting"""
    
    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='financial_summaries')
    
    # Period
    year = models.IntegerField()
    month = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    
    # Financial metrics
    total_income = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_expenses = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    net_profit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Asset metrics
    total_assets = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Tax metrics
    turnover_tax_due = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Tracking
    calculated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-year', '-month']
        unique_together = ['user', 'year', 'month']
        indexes = [
            models.Index(fields=['user', 'year', 'month']),
        ]
    
    def __str__(self):
        return f"Financial Summary {self.year}-{self.month:02d} - Profit: K{self.net_profit}"
    
    def calculate_summary(self):
        """Calculate financial summary for the period"""
        from django.db.models import Sum
        from datetime import date
        
        # Get date range for the month
        start_date = date(self.year, self.month, 1)
        if self.month == 12:
            end_date = date(self.year + 1, 1, 1)
        else:
            end_date = date(self.year, self.month + 1, 1)
        
        # Calculate income
        income_total = IncomeRecord.objects.filter(
            user=self.user,
            income_date__gte=start_date,
            income_date__lt=end_date
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Calculate expenses
        expense_total = Expense.objects.filter(
            user=self.user,
            expense_date__gte=start_date,
            expense_date__lt=end_date,
            payment_status='paid'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Calculate assets
        asset_total = Asset.objects.filter(
            user=self.user,
            status='active'
        ).aggregate(
            total=Sum('current_value')
        )['total'] or Decimal('0.00')
        
        # If current_value is None, use purchase_value
        if asset_total == Decimal('0.00'):
            asset_total = Asset.objects.filter(
                user=self.user,
                status='active'
            ).aggregate(
                total=Sum('purchase_value')
            )['total'] or Decimal('0.00')
        
        # Get turnover tax
        try:
            tax_record = TurnoverTaxRecord.objects.get(
                user=self.user,
                year=self.year,
                month=self.month
            )
            tax_due = tax_record.tax_due
        except TurnoverTaxRecord.DoesNotExist:
            tax_due = Decimal('0.00')
        
        # Update summary
        self.total_income = income_total
        self.total_expenses = expense_total
        self.net_profit = income_total - expense_total
        self.total_assets = asset_total
        self.turnover_tax_due = tax_due
        
        self.save()
        return self
