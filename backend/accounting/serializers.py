from rest_framework import serializers
from decimal import Decimal
from django.utils import timezone
from .models import (
    Expense, ExpenseCategory, Asset, AssetCategory, 
    IncomeRecord, TurnoverTaxRecord, FinancialSummary
)


class ExpenseCategorySerializer(serializers.ModelSerializer):
    """Serializer for expense categories"""
    display_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ExpenseCategory
        fields = ['name', 'display_name', 'description', 'is_active']
    
    def get_display_name(self, obj):
        return obj.get_name_display()


class ExpenseSerializer(serializers.ModelSerializer):
    """Serializer for viewing expenses"""
    category_name = serializers.CharField(source='category.get_name_display', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    expense_type_display = serializers.CharField(source='get_expense_type_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    
    class Meta:
        model = Expense
        fields = [
            'id', 'name', 'category', 'category_name', 'amount', 'expense_type',
            'expense_type_display', 'recurrence', 'expense_date', 'due_date',
            'payment_date', 'payment_status', 'payment_status_display', 'vendor',
            'reference_number', 'notes', 'is_overdue', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ExpenseCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating expenses"""
    
    class Meta:
        model = Expense
        fields = [
            'name', 'category', 'amount', 'expense_type', 'recurrence',
            'expense_date', 'due_date', 'payment_date', 'payment_status',
            'vendor', 'reference_number', 'notes'
        ]
    
    def validate(self, data):
        """Validate expense data"""
        # If expense type is recurring, recurrence must be specified
        if data.get('expense_type') == 'recurring' and not data.get('recurrence'):
            raise serializers.ValidationError(
                "Recurrence pattern must be specified for recurring expenses"
            )
        
        # Payment date should not be before expense date
        if data.get('payment_date') and data.get('expense_date'):
            if data['payment_date'] < data['expense_date']:
                raise serializers.ValidationError(
                    "Payment date cannot be before expense date"
                )
        
        # If payment status is paid, payment date should be provided
        if data.get('payment_status') == 'paid' and not data.get('payment_date'):
            data['payment_date'] = timezone.now().date()
        
        return data
    
    def create(self, validated_data):
        """Create expense with user assignment"""
        user = self.context['request'].user
        expense = Expense.objects.create(user=user, **validated_data)
        return expense


class AssetCategorySerializer(serializers.ModelSerializer):
    """Serializer for asset categories"""
    display_name = serializers.SerializerMethodField()
    
    class Meta:
        model = AssetCategory
        fields = ['name', 'display_name', 'description', 'is_active']
    
    def get_display_name(self, obj):
        return obj.get_name_display()


class AssetSerializer(serializers.ModelSerializer):
    """Serializer for viewing assets"""
    category_name = serializers.CharField(source='category.get_name_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    depreciation_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    depreciation_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    
    class Meta:
        model = Asset
        fields = [
            'id', 'name', 'category', 'category_name', 'purchase_value', 'current_value',
            'purchase_date', 'status', 'status_display', 'disposal_date', 'vendor',
            'serial_number', 'location', 'notes', 'depreciation_amount',
            'depreciation_percentage', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AssetCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating assets"""
    
    class Meta:
        model = Asset
        fields = [
            'name', 'category', 'purchase_value', 'current_value', 'purchase_date',
            'status', 'disposal_date', 'vendor', 'serial_number', 'location', 'notes'
        ]
    
    def validate(self, data):
        """Validate asset data"""
        # Current value should not exceed purchase value
        if data.get('current_value') and data.get('purchase_value'):
            if data['current_value'] > data['purchase_value']:
                raise serializers.ValidationError(
                    "Current value cannot exceed purchase value"
                )
        
        # Disposal date should be after purchase date
        if data.get('disposal_date') and data.get('purchase_date'):
            if data['disposal_date'] < data['purchase_date']:
                raise serializers.ValidationError(
                    "Disposal date cannot be before purchase date"
                )
        
        # If status is disposed, disposal date should be provided
        if data.get('status') == 'disposed' and not data.get('disposal_date'):
            data['disposal_date'] = timezone.now().date()
        
        return data
    
    def create(self, validated_data):
        """Create asset with user assignment"""
        user = self.context['request'].user
        asset = Asset.objects.create(user=user, **validated_data)
        return asset


class IncomeRecordSerializer(serializers.ModelSerializer):
    """Serializer for income records"""
    source_display = serializers.CharField(source='get_source_display', read_only=True)
    
    class Meta:
        model = IncomeRecord
        fields = [
            'id', 'source', 'source_display', 'amount', 'income_date',
            'description', 'sale_id', 'service_record_id', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class TurnoverTaxRecordSerializer(serializers.ModelSerializer):
    """Serializer for turnover tax records"""
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    is_eligible = serializers.BooleanField(source='is_eligible_for_turnover_tax', read_only=True)
    
    class Meta:
        model = TurnoverTaxRecord
        fields = [
            'id', 'year', 'month', 'total_revenue', 'tax_free_threshold',
            'taxable_amount', 'tax_rate', 'tax_due', 'payment_status',
            'payment_status_display', 'payment_date', 'payment_reference',
            'is_eligible', 'calculated_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'taxable_amount', 'tax_due', 'calculated_at', 'updated_at'
        ]


class FinancialSummarySerializer(serializers.ModelSerializer):
    """Serializer for financial summaries"""
    
    class Meta:
        model = FinancialSummary
        fields = [
            'id', 'year', 'month', 'total_income', 'total_expenses',
            'net_profit', 'total_assets', 'turnover_tax_due',
            'calculated_at', 'updated_at'
        ]
        read_only_fields = ['id', 'calculated_at', 'updated_at']


class ProfitLossReportSerializer(serializers.Serializer):
    """Serializer for Profit & Loss reports"""
    period_start = serializers.DateField()
    period_end = serializers.DateField()
    total_income = serializers.DecimalField(max_digits=12, decimal_places=2)
    income_breakdown = serializers.DictField()
    total_expenses = serializers.DecimalField(max_digits=12, decimal_places=2)
    expense_breakdown = serializers.DictField()
    net_profit = serializers.DecimalField(max_digits=12, decimal_places=2)
    profit_margin = serializers.DecimalField(max_digits=5, decimal_places=2)


class CashFlowReportSerializer(serializers.Serializer):
    """Serializer for Cash Flow reports"""
    period_start = serializers.DateField()
    period_end = serializers.DateField()
    opening_balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_inflows = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_outflows = serializers.DecimalField(max_digits=12, decimal_places=2)
    net_cash_flow = serializers.DecimalField(max_digits=12, decimal_places=2)
    closing_balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    monthly_breakdown = serializers.ListField()


class TurnoverTaxReportSerializer(serializers.Serializer):
    """Serializer for Turnover Tax reports"""
    year = serializers.IntegerField()
    annual_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    annual_tax_due = serializers.DecimalField(max_digits=12, decimal_places=2)
    monthly_breakdown = serializers.ListField()
    is_eligible_for_turnover_tax = serializers.BooleanField()
    exceeds_annual_threshold = serializers.BooleanField()


class DashboardSerializer(serializers.Serializer):
    """Serializer for financial dashboard data"""
    # Current month metrics
    current_month_income = serializers.DecimalField(max_digits=12, decimal_places=2)
    current_month_expenses = serializers.DecimalField(max_digits=12, decimal_places=2)
    current_month_profit = serializers.DecimalField(max_digits=12, decimal_places=2)
    current_month_tax_due = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    # Year-to-date metrics
    ytd_income = serializers.DecimalField(max_digits=12, decimal_places=2)
    ytd_expenses = serializers.DecimalField(max_digits=12, decimal_places=2)
    ytd_profit = serializers.DecimalField(max_digits=12, decimal_places=2)
    ytd_tax_due = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    # Asset metrics
    total_assets = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    # Outstanding items
    unpaid_expenses = serializers.IntegerField()
    overdue_expenses = serializers.IntegerField()
    unpaid_taxes = serializers.IntegerField()
    
    # Charts data
    monthly_profit_trend = serializers.ListField()
    expense_breakdown = serializers.DictField()
    income_sources = serializers.DictField()
    
    # Recent activities
    recent_income = serializers.ListField()
    recent_expenses = serializers.ListField()
    
    # Alerts
    alerts = serializers.ListField()


class ExpenseAnalysisSerializer(serializers.Serializer):
    """Serializer for expense analysis reports"""
    period_start = serializers.DateField()
    period_end = serializers.DateField()
    total_expenses = serializers.DecimalField(max_digits=12, decimal_places=2)
    category_breakdown = serializers.DictField()
    monthly_trend = serializers.ListField()
    top_expenses = serializers.ListField()
    recurring_vs_one_time = serializers.DictField()
    payment_status_breakdown = serializers.DictField()
