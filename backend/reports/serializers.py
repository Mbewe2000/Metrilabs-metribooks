from rest_framework import serializers
from decimal import Decimal
from datetime import date, datetime, timedelta
from django.utils import timezone
from django.db.models import Sum, Count, Avg, Q

from .models import ReportSnapshot, ReportTemplate, BusinessMetric


class ReportSnapshotSerializer(serializers.ModelSerializer):
    """Serializer for report snapshots"""
    
    profit_margin_percentage = serializers.SerializerMethodField()
    expense_ratio_percentage = serializers.SerializerMethodField()
    tax_rate_percentage = serializers.SerializerMethodField()
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    period_days = serializers.SerializerMethodField()
    
    class Meta:
        model = ReportSnapshot
        fields = [
            'id', 'report_type', 'report_type_display', 'period_start', 'period_end',
            'total_income', 'total_expenses', 'net_profit', 'total_sales_count',
            'total_sales_amount', 'average_sale_value', 'total_service_hours',
            'total_service_revenue', 'taxable_income', 'turnover_tax_due',
            'profit_margin_percentage', 'expense_ratio_percentage', 'tax_rate_percentage',
            'period_days', 'additional_data', 'generated_at', 'is_cached'
        ]
        read_only_fields = [
            'id', 'generated_at', 'profit_margin_percentage', 
            'expense_ratio_percentage', 'tax_rate_percentage', 'period_days'
        ]
    
    def get_profit_margin_percentage(self, obj):
        return obj.get_profit_margin_percentage()
    
    def get_expense_ratio_percentage(self, obj):
        return obj.get_expense_ratio_percentage()
    
    def get_tax_rate_percentage(self, obj):
        return obj.get_tax_rate_percentage()
    
    def get_period_days(self, obj):
        """Calculate number of days in the reporting period"""
        return (obj.period_end - obj.period_start).days + 1


class ReportTemplateSerializer(serializers.ModelSerializer):
    """Serializer for report templates"""
    
    frequency_display = serializers.CharField(source='get_frequency_display', read_only=True)
    
    class Meta:
        model = ReportTemplate
        fields = [
            'id', 'name', 'description', 'report_types', 'frequency', 'frequency_display',
            'auto_generate', 'include_sales', 'include_services', 'include_expenses',
            'include_assets', 'include_tax_analysis', 'email_recipients',
            'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_report_types(self, value):
        """Validate report types"""
        valid_types = [choice[0] for choice in ReportSnapshot.REPORT_TYPES]
        for report_type in value:
            if report_type not in valid_types:
                raise serializers.ValidationError(f"Invalid report type: {report_type}")
        return value
    
    def validate_email_recipients(self, value):
        """Validate email addresses"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Email recipients must be a list")
        
        for email in value:
            if not isinstance(email, str) or '@' not in email:
                raise serializers.ValidationError(f"Invalid email address: {email}")
        return value


class BusinessMetricSerializer(serializers.ModelSerializer):
    """Serializer for business metrics"""
    
    metric_type_display = serializers.CharField(source='get_metric_type_display', read_only=True)
    trend_direction = serializers.SerializerMethodField()
    is_positive_change = serializers.SerializerMethodField()
    
    class Meta:
        model = BusinessMetric
        fields = [
            'id', 'metric_type', 'metric_type_display', 'metric_date', 'value',
            'percentage_value', 'previous_period_value', 'change_percentage',
            'trend_direction', 'is_positive_change', 'notes', 'metadata',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'trend_direction', 'is_positive_change'
        ]
    
    def get_trend_direction(self, obj):
        return obj.get_trend_direction()
    
    def get_is_positive_change(self, obj):
        return obj.is_positive_change()


class ProfitLossReportSerializer(serializers.Serializer):
    """Serializer for Profit & Loss reports"""
    
    period_start = serializers.DateField()
    period_end = serializers.DateField()
    
    # Income section
    sales_revenue = serializers.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    service_revenue = serializers.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    other_income = serializers.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_income = serializers.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Expenses section
    cost_of_goods_sold = serializers.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    operating_expenses = serializers.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    administrative_expenses = serializers.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_expenses = serializers.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Profit calculations
    gross_profit = serializers.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    net_profit = serializers.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Percentages
    gross_margin_percentage = serializers.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    net_margin_percentage = serializers.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    
    # Additional metrics
    number_of_transactions = serializers.IntegerField(default=0)
    average_transaction_value = serializers.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))


class CashFlowReportSerializer(serializers.Serializer):
    """Serializer for Cash Flow reports"""
    
    period_start = serializers.DateField()
    period_end = serializers.DateField()
    
    # Cash inflows
    cash_from_sales = serializers.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    cash_from_services = serializers.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    other_cash_inflows = serializers.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_cash_inflows = serializers.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Cash outflows
    cash_for_expenses = serializers.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    cash_for_assets = serializers.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    cash_for_taxes = serializers.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_cash_outflows = serializers.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Net cash flow
    net_cash_flow = serializers.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Daily breakdown for trends
    daily_inflows = serializers.ListField(child=serializers.DictField(), required=False)
    daily_outflows = serializers.ListField(child=serializers.DictField(), required=False)


class SalesTrendReportSerializer(serializers.Serializer):
    """Serializer for Sales Trend reports"""
    
    period_start = serializers.DateField()
    period_end = serializers.DateField()
    period_type = serializers.CharField(max_length=20, default='monthly')  # daily, weekly, monthly
    
    # Trend data
    trend_data = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of trend data points with date and values"
    )
    
    # Summary statistics
    total_sales = serializers.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    average_sales = serializers.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    highest_sales_period = serializers.DictField(required=False)
    lowest_sales_period = serializers.DictField(required=False)
    
    # Growth metrics
    growth_rate = serializers.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    trend_direction = serializers.CharField(max_length=20, default='stable')  # up, down, stable


class ExpenseTrendReportSerializer(serializers.Serializer):
    """Serializer for Expense Trend reports"""
    
    period_start = serializers.DateField()
    period_end = serializers.DateField()
    period_type = serializers.CharField(max_length=20, default='monthly')
    
    # Trend data
    trend_data = serializers.ListField(child=serializers.DictField())
    
    # Category breakdown
    expense_categories = serializers.ListField(child=serializers.DictField())
    
    # Summary statistics
    total_expenses = serializers.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    average_expenses = serializers.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    highest_expense_period = serializers.DictField(required=False)
    lowest_expense_period = serializers.DictField(required=False)


class TaxSummaryReportSerializer(serializers.Serializer):
    """Serializer for Tax Summary reports"""
    
    period_start = serializers.DateField()
    period_end = serializers.DateField()
    
    # Income breakdown
    total_revenue = serializers.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    tax_free_allowance = serializers.DecimalField(max_digits=15, decimal_places=2, default=Decimal('1000.00'))
    taxable_income = serializers.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Tax calculations
    turnover_tax_rate = serializers.DecimalField(max_digits=5, decimal_places=2, default=Decimal('5.00'))
    turnover_tax_due = serializers.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Monthly breakdown
    monthly_breakdown = serializers.ListField(child=serializers.DictField())
    
    # Compliance status
    annual_turnover_limit = serializers.DecimalField(max_digits=15, decimal_places=2, default=Decimal('5000000.00'))
    current_annual_turnover = serializers.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    is_eligible_for_turnover_tax = serializers.BooleanField(default=True)


class BusinessOverviewReportSerializer(serializers.Serializer):
    """Serializer for comprehensive business overview"""
    
    period_start = serializers.DateField()
    period_end = serializers.DateField()
    
    # Key financial metrics
    total_revenue = serializers.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_expenses = serializers.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    net_profit = serializers.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    profit_margin = serializers.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    
    # Operational metrics
    total_sales_transactions = serializers.IntegerField(default=0)
    total_service_hours = serializers.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_products_sold = serializers.IntegerField(default=0)
    
    # Growth indicators
    revenue_growth = serializers.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    expense_growth = serializers.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    customer_growth = serializers.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    
    # Tax information
    total_tax_due = serializers.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    effective_tax_rate = serializers.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    
    # Top performers
    top_selling_products = serializers.ListField(child=serializers.DictField(), required=False)
    top_services = serializers.ListField(child=serializers.DictField(), required=False)
    top_expense_categories = serializers.ListField(child=serializers.DictField(), required=False)


class ReportGenerationRequestSerializer(serializers.Serializer):
    """Serializer for report generation requests"""
    
    report_type = serializers.ChoiceField(choices=ReportSnapshot.REPORT_TYPES)
    period_start = serializers.DateField()
    period_end = serializers.DateField()
    force_regenerate = serializers.BooleanField(default=False)
    include_trends = serializers.BooleanField(default=True)
    include_comparisons = serializers.BooleanField(default=True)
    
    def validate(self, data):
        """Validate the date range"""
        if data['period_start'] > data['period_end']:
            raise serializers.ValidationError("Start date must be before end date")
        
        # Check if period is reasonable (not more than 5 years)
        max_days = 365 * 5
        if (data['period_end'] - data['period_start']).days > max_days:
            raise serializers.ValidationError("Reporting period cannot exceed 5 years")
        
        return data
