from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid
from datetime import date, datetime

User = settings.AUTH_USER_MODEL


class ReportSnapshot(models.Model):
    """
    Store snapshot data for reports to improve performance
    and enable historical comparisons
    """
    REPORT_TYPES = [
        ('profit_loss', 'Profit & Loss'),
        ('cash_flow', 'Cash Flow'),
        ('sales_trend', 'Sales Trend'),
        ('expense_trend', 'Expense Trend'),
        ('tax_summary', 'Tax Summary'),
        ('business_overview', 'Business Overview'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='report_snapshots'
    )
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    period_start = models.DateField(help_text="Start date of the reporting period")
    period_end = models.DateField(help_text="End date of the reporting period")
    
    # Financial metrics
    total_income = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Total income for the period"
    )
    total_expenses = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Total expenses for the period"
    )
    net_profit = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Net profit (income - expenses)"
    )
    
    # Sales metrics
    total_sales_count = models.IntegerField(default=0, help_text="Number of sales transactions")
    total_sales_amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Total sales amount"
    )
    average_sale_value = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Average value per sale"
    )
    
    # Service metrics
    total_service_hours = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Total service hours worked"
    )
    total_service_revenue = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Total revenue from services"
    )
    
    # Tax metrics
    taxable_income = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Income subject to turnover tax"
    )
    turnover_tax_due = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Turnover tax owed for the period"
    )
    
    # Additional JSON data for flexible reporting
    additional_data = models.JSONField(
        default=dict, 
        blank=True,
        help_text="Additional report data in JSON format"
    )
    
    # Metadata
    generated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_cached = models.BooleanField(
        default=True, 
        help_text="Whether this is a cached report for performance"
    )
    
    class Meta:
        db_table = 'report_snapshots'
        verbose_name = 'Report Snapshot'
        verbose_name_plural = 'Report Snapshots'
        ordering = ['-period_end', '-generated_at']
        indexes = [
            models.Index(fields=['user', 'report_type']),
            models.Index(fields=['user', 'period_start', 'period_end']),
            models.Index(fields=['user', 'report_type', 'period_start']),
        ]
        unique_together = [('user', 'report_type', 'period_start', 'period_end')]
    
    def __str__(self):
        return f"{self.get_report_type_display()} - {self.period_start} to {self.period_end}"
    
    def get_profit_margin_percentage(self):
        """Calculate profit margin as percentage"""
        if self.total_income > 0:
            return round((self.net_profit / self.total_income) * 100, 2)
        return Decimal('0.00')
    
    def get_expense_ratio_percentage(self):
        """Calculate expense ratio as percentage of income"""
        if self.total_income > 0:
            return round((self.total_expenses / self.total_income) * 100, 2)
        return Decimal('0.00')
    
    def get_tax_rate_percentage(self):
        """Calculate effective tax rate"""
        if self.taxable_income > 0:
            return round((self.turnover_tax_due / self.taxable_income) * 100, 2)
        return Decimal('0.00')


class ReportTemplate(models.Model):
    """
    Custom report templates that users can create and reuse
    """
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
        ('custom', 'Custom Period'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='report_templates'
    )
    name = models.CharField(max_length=200, help_text="Template name")
    description = models.TextField(blank=True, help_text="Template description")
    
    # Report configuration
    report_types = models.JSONField(
        default=list,
        help_text="List of report types to include"
    )
    frequency = models.CharField(
        max_length=20, 
        choices=FREQUENCY_CHOICES, 
        default='monthly'
    )
    auto_generate = models.BooleanField(
        default=False,
        help_text="Whether to automatically generate this report"
    )
    
    # Filters and parameters
    include_sales = models.BooleanField(default=True)
    include_services = models.BooleanField(default=True)
    include_expenses = models.BooleanField(default=True)
    include_assets = models.BooleanField(default=False)
    include_tax_analysis = models.BooleanField(default=True)
    
    # Email settings
    email_recipients = models.JSONField(
        default=list,
        blank=True,
        help_text="Email addresses to send reports to"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'report_templates'
        verbose_name = 'Report Template'
        verbose_name_plural = 'Report Templates'
        ordering = ['name']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['user', 'frequency']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_frequency_display()})"


class BusinessMetric(models.Model):
    """
    Store key business metrics for tracking over time
    """
    METRIC_TYPES = [
        ('revenue_growth', 'Revenue Growth Rate'),
        ('profit_margin', 'Profit Margin'),
        ('customer_acquisition', 'Customer Acquisition'),
        ('average_order_value', 'Average Order Value'),
        ('expense_ratio', 'Expense Ratio'),
        ('inventory_turnover', 'Inventory Turnover'),
        ('service_utilization', 'Service Utilization'),
        ('tax_efficiency', 'Tax Efficiency'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='business_metrics'
    )
    metric_type = models.CharField(max_length=30, choices=METRIC_TYPES)
    metric_date = models.DateField(default=date.today)
    
    # Metric values
    value = models.DecimalField(
        max_digits=15, 
        decimal_places=4, 
        help_text="Primary metric value"
    )
    percentage_value = models.DecimalField(
        max_digits=8, 
        decimal_places=4, 
        null=True, 
        blank=True,
        help_text="Percentage representation if applicable"
    )
    
    # Comparison data
    previous_period_value = models.DecimalField(
        max_digits=15, 
        decimal_places=4, 
        null=True, 
        blank=True,
        help_text="Value from previous period for comparison"
    )
    change_percentage = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Percentage change from previous period"
    )
    
    # Additional context
    notes = models.TextField(blank=True, help_text="Additional notes about this metric")
    metadata = models.JSONField(
        default=dict, 
        blank=True,
        help_text="Additional metric metadata"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'business_metrics'
        verbose_name = 'Business Metric'
        verbose_name_plural = 'Business Metrics'
        ordering = ['-metric_date', 'metric_type']
        indexes = [
            models.Index(fields=['user', 'metric_type']),
            models.Index(fields=['user', 'metric_date']),
            models.Index(fields=['user', 'metric_type', 'metric_date']),
        ]
        unique_together = [('user', 'metric_type', 'metric_date')]
    
    def __str__(self):
        return f"{self.get_metric_type_display()} - {self.metric_date}: {self.value}"
    
    def get_trend_direction(self):
        """Get trend direction based on change percentage"""
        if self.change_percentage is None:
            return 'neutral'
        elif self.change_percentage > 0:
            return 'up'
        elif self.change_percentage < 0:
            return 'down'
        else:
            return 'stable'
    
    def is_positive_change(self):
        """Determine if the change is positive for business"""
        # For most metrics, positive change is good
        positive_metrics = [
            'revenue_growth', 'profit_margin', 'customer_acquisition', 
            'average_order_value', 'inventory_turnover', 'service_utilization'
        ]
        # For expense ratio, lower is better
        negative_metrics = ['expense_ratio']
        
        if self.change_percentage is None:
            return None
        
        if self.metric_type in positive_metrics:
            return self.change_percentage > 0
        elif self.metric_type in negative_metrics:
            return self.change_percentage < 0
        else:
            return None
