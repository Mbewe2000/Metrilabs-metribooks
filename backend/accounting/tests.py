from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta

from .models import (
    ExpenseCategory, Expense, AssetCategory, Asset,
    IncomeRecord, TurnoverTaxRecord, FinancialSummary
)

User = get_user_model()


class ExpenseModelTest(TestCase):
    """Test Expense model functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123'
        )
        
        self.category = ExpenseCategory.objects.create(
            name='operational',
            description='Operational expenses'
        )
    
    def test_expense_creation(self):
        """Test creating an expense"""
        expense = Expense.objects.create(
            user=self.user,
            name='Office Rent',
            category=self.category,
            amount=Decimal('2000.00'),
            expense_type='recurring',
            recurrence='monthly',
            expense_date=date.today(),
            payment_status='paid'
        )
        
        self.assertEqual(expense.name, 'Office Rent')
        self.assertEqual(expense.amount, Decimal('2000.00'))
        self.assertEqual(expense.user, self.user)
        self.assertEqual(expense.category, self.category)
        self.assertEqual(expense.expense_type, 'recurring')
        self.assertEqual(expense.recurrence, 'monthly')
        self.assertEqual(expense.payment_status, 'paid')
    
    def test_expense_overdue_detection(self):
        """Test overdue expense detection"""
        # Create overdue expense
        past_date = date.today() - timedelta(days=7)
        expense = Expense.objects.create(
            user=self.user,
            name='Overdue Expense',
            category=self.category,
            amount=Decimal('500.00'),
            expense_date=past_date,
            due_date=past_date,
            payment_status='unpaid'
        )
        
        self.assertTrue(expense.is_overdue)
    
    def test_expense_string_representation(self):
        """Test expense string representation"""
        expense = Expense.objects.create(
            user=self.user,
            name='Test Expense',
            category=self.category,
            amount=Decimal('100.00'),
            expense_date=date.today()
        )
        
        expected = f"Test Expense - K100.00 ({date.today()})"
        self.assertEqual(str(expense), expected)


class AssetModelTest(TestCase):
    """Test Asset model functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123'
        )
        
        self.category = AssetCategory.objects.create(
            name='equipment',
            description='Equipment and machinery'
        )
    
    def test_asset_creation(self):
        """Test creating an asset"""
        asset = Asset.objects.create(
            user=self.user,
            name='Office Computer',
            category=self.category,
            purchase_value=Decimal('5000.00'),
            current_value=Decimal('3000.00'),
            purchase_date=date.today(),
            status='active',
            vendor='TechCorp'
        )
        
        self.assertEqual(asset.name, 'Office Computer')
        self.assertEqual(asset.purchase_value, Decimal('5000.00'))
        self.assertEqual(asset.current_value, Decimal('3000.00'))
        self.assertEqual(asset.user, self.user)
        self.assertEqual(asset.category, self.category)
        self.assertEqual(asset.status, 'active')
        self.assertEqual(asset.vendor, 'TechCorp')
    
    def test_asset_depreciation_calculation(self):
        """Test asset depreciation calculations"""
        asset = Asset.objects.create(
            user=self.user,
            name='Laptop',
            category=self.category,
            purchase_value=Decimal('10000.00'),
            current_value=Decimal('6000.00'),
            purchase_date=date.today()
        )
        
        # Test depreciation amount
        self.assertEqual(asset.depreciation_amount, Decimal('4000.00'))
        
        # Test depreciation percentage
        self.assertEqual(asset.depreciation_percentage, Decimal('40.00'))
    
    def test_asset_string_representation(self):
        """Test asset string representation"""
        asset = Asset.objects.create(
            user=self.user,
            name='Test Asset',
            category=self.category,
            purchase_value=Decimal('1000.00'),
            purchase_date=date.today()
        )
        
        expected = f"Test Asset - K1000.00 ({date.today()})"
        self.assertEqual(str(asset), expected)


class IncomeRecordModelTest(TestCase):
    """Test IncomeRecord model functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123'
        )
    
    def test_income_record_creation(self):
        """Test creating an income record"""
        income = IncomeRecord.objects.create(
            user=self.user,
            source='sales',
            amount=Decimal('1500.00'),
            income_date=date.today(),
            description='Product Sale #001'
        )
        
        self.assertEqual(income.source, 'sales')
        self.assertEqual(income.amount, Decimal('1500.00'))
        self.assertEqual(income.user, self.user)
        self.assertEqual(income.description, 'Product Sale #001')
    
    def test_income_record_string_representation(self):
        """Test income record string representation"""
        income = IncomeRecord.objects.create(
            user=self.user,
            source='services',
            amount=Decimal('2000.00'),
            income_date=date.today(),
            description='Service Income'
        )
        
        expected = f"Service Income - K2000.00 ({date.today()})"
        self.assertEqual(str(income), expected)


class TurnoverTaxRecordModelTest(TestCase):
    """Test TurnoverTaxRecord model functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123'
        )
    
    def test_turnover_tax_calculation(self):
        """Test turnover tax calculation"""
        # Test case 1: Revenue below threshold
        tax_record = TurnoverTaxRecord.objects.create(
            user=self.user,
            year=2025,
            month=7,
            total_revenue=Decimal('800.00')
        )
        
        tax_record.calculate_tax()
        
        # Should be 0 tax as revenue is below K1,000 threshold
        self.assertEqual(tax_record.taxable_amount, Decimal('0.00'))
        self.assertEqual(tax_record.tax_due, Decimal('0.00'))
        
        # Test case 2: Revenue above threshold
        tax_record.total_revenue = Decimal('8000.00')
        tax_record.calculate_tax()
        
        # K8,000 - K1,000 = K7,000 taxable @ 5% = K350 tax
        self.assertEqual(tax_record.taxable_amount, Decimal('7000.00'))
        self.assertEqual(tax_record.tax_due, Decimal('350.00'))
    
    def test_annual_turnover_calculation(self):
        """Test annual turnover calculation"""
        # Create multiple monthly records
        TurnoverTaxRecord.objects.create(
            user=self.user,
            year=2025,
            month=1,
            total_revenue=Decimal('50000.00')
        )
        
        TurnoverTaxRecord.objects.create(
            user=self.user,
            year=2025,
            month=2,
            total_revenue=Decimal('60000.00')
        )
        
        annual_total = TurnoverTaxRecord.get_annual_turnover(self.user, 2025)
        self.assertEqual(annual_total, Decimal('110000.00'))
    
    def test_turnover_tax_eligibility(self):
        """Test turnover tax eligibility checking"""
        # Create records totaling under K5M
        tax_record = TurnoverTaxRecord.objects.create(
            user=self.user,
            year=2025,
            month=7,
            total_revenue=Decimal('400000.00')
        )
        
        # Should be eligible as under K5M annual threshold
        self.assertTrue(tax_record.is_eligible_for_turnover_tax)
    
    def test_turnover_tax_string_representation(self):
        """Test turnover tax string representation"""
        tax_record = TurnoverTaxRecord.objects.create(
            user=self.user,
            year=2025,
            month=7,
            total_revenue=Decimal('8000.00')
        )
        tax_record.calculate_tax()
        
        expected = "Turnover Tax 2025-07 - K350.00"
        self.assertEqual(str(tax_record), expected)


class FinancialSummaryModelTest(TestCase):
    """Test FinancialSummary model functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123'
        )
        
        # Create test data
        self.expense_category = ExpenseCategory.objects.create(
            name='operational',
            description='Operational expenses'
        )
        
        self.asset_category = AssetCategory.objects.create(
            name='equipment',
            description='Equipment'
        )
        
        # Create income records for July 2025
        IncomeRecord.objects.create(
            user=self.user,
            source='sales',
            amount=Decimal('5000.00'),
            income_date=date(2025, 7, 15),
            description='Sales income'
        )
        
        IncomeRecord.objects.create(
            user=self.user,
            source='services',
            amount=Decimal('3000.00'),
            income_date=date(2025, 7, 20),
            description='Service income'
        )
        
        # Create expenses for July 2025
        Expense.objects.create(
            user=self.user,
            name='Office Rent',
            category=self.expense_category,
            amount=Decimal('2000.00'),
            expense_date=date(2025, 7, 1),
            payment_status='paid'
        )
        
        Expense.objects.create(
            user=self.user,
            name='Utilities',
            category=self.expense_category,
            amount=Decimal('500.00'),
            expense_date=date(2025, 7, 10),
            payment_status='paid'
        )
        
        # Create assets
        Asset.objects.create(
            user=self.user,
            name='Computer',
            category=self.asset_category,
            purchase_value=Decimal('10000.00'),
            current_value=Decimal('8000.00'),
            purchase_date=date(2025, 6, 1),
            status='active'
        )
        
        # Create turnover tax record
        tax_record = TurnoverTaxRecord.objects.create(
            user=self.user,
            year=2025,
            month=7,
            total_revenue=Decimal('8000.00')
        )
        tax_record.calculate_tax()
    
    def test_financial_summary_calculation(self):
        """Test financial summary calculation"""
        # Try to get existing summary first (created by signals), or create new one
        summary, created = FinancialSummary.objects.get_or_create(
            user=self.user,
            year=2025,
            month=7,
            defaults={}
        )
        
        summary.calculate_summary()
        
        # Check calculated values
        self.assertEqual(summary.total_income, Decimal('8000.00'))  # 5000 + 3000
        self.assertEqual(summary.total_expenses, Decimal('2500.00'))  # 2000 + 500
        self.assertEqual(summary.net_profit, Decimal('5500.00'))  # 8000 - 2500
        self.assertEqual(summary.total_assets, Decimal('8000.00'))  # Current value of computer
        self.assertEqual(summary.turnover_tax_due, Decimal('350.00'))  # (8000-1000) * 5%
    
    def test_financial_summary_string_representation(self):
        """Test financial summary string representation"""
        # Use a different month to avoid conflict with other test
        summary = FinancialSummary.objects.create(
            user=self.user,
            year=2025,
            month=8,
            net_profit=Decimal('5500.00')
        )
        
        expected = "Financial Summary 2025-08 - Profit: K5500.00"
        self.assertEqual(str(summary), expected)


class CategoryModelTest(TestCase):
    """Test category models"""
    
    def test_expense_category_creation(self):
        """Test expense category creation"""
        category = ExpenseCategory.objects.create(
            name='utilities',
            description='Utility expenses',
            is_active=True
        )
        
        self.assertEqual(category.name, 'utilities')
        self.assertEqual(category.description, 'Utility expenses')
        self.assertTrue(category.is_active)
        self.assertEqual(str(category), 'Utilities')
    
    def test_asset_category_creation(self):
        """Test asset category creation"""
        category = AssetCategory.objects.create(
            name='vehicles',
            description='Company vehicles',
            is_active=True
        )
        
        self.assertEqual(category.name, 'vehicles')
        self.assertEqual(category.description, 'Company vehicles')
        self.assertTrue(category.is_active)
        self.assertEqual(str(category), 'Vehicles')


class UserIsolationTest(TestCase):
    """Test user data isolation"""
    
    def setUp(self):
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='testpass123'
        )
        
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123'
        )
        
        self.category = ExpenseCategory.objects.create(
            name='operational',
            description='Operational expenses'
        )
    
    def test_expense_user_isolation(self):
        """Test that users can only see their own expenses"""
        # Create expenses for both users
        expense1 = Expense.objects.create(
            user=self.user1,
            name='User 1 Expense',
            category=self.category,
            amount=Decimal('1000.00'),
            expense_date=date.today()
        )
        
        expense2 = Expense.objects.create(
            user=self.user2,
            name='User 2 Expense',
            category=self.category,
            amount=Decimal('2000.00'),
            expense_date=date.today()
        )
        
        # Test user1 can only see their expense
        user1_expenses = Expense.objects.filter(user=self.user1)
        self.assertEqual(user1_expenses.count(), 1)
        self.assertEqual(user1_expenses.first(), expense1)
        
        # Test user2 can only see their expense
        user2_expenses = Expense.objects.filter(user=self.user2)
        self.assertEqual(user2_expenses.count(), 1)
        self.assertEqual(user2_expenses.first(), expense2)
    
    def test_income_user_isolation(self):
        """Test that users can only see their own income"""
        # Create income for both users
        income1 = IncomeRecord.objects.create(
            user=self.user1,
            source='sales',
            amount=Decimal('5000.00'),
            income_date=date.today(),
            description='User 1 Income'
        )
        
        income2 = IncomeRecord.objects.create(
            user=self.user2,
            source='sales',
            amount=Decimal('3000.00'),
            income_date=date.today(),
            description='User 2 Income'
        )
        
        # Test user isolation
        user1_income = IncomeRecord.objects.filter(user=self.user1)
        self.assertEqual(user1_income.count(), 1)
        self.assertEqual(user1_income.first(), income1)
        
        user2_income = IncomeRecord.objects.filter(user=self.user2)
        self.assertEqual(user2_income.count(), 1)
        self.assertEqual(user2_income.first(), income2)
    
    def test_turnover_tax_user_isolation(self):
        """Test that users can only see their own tax records"""
        # Create tax records for both users
        tax1 = TurnoverTaxRecord.objects.create(
            user=self.user1,
            year=2025,
            month=7,
            total_revenue=Decimal('8000.00')
        )
        
        tax2 = TurnoverTaxRecord.objects.create(
            user=self.user2,
            year=2025,
            month=7,
            total_revenue=Decimal('6000.00')
        )
        
        # Test user isolation
        user1_tax = TurnoverTaxRecord.objects.filter(user=self.user1)
        self.assertEqual(user1_tax.count(), 1)
        self.assertEqual(user1_tax.first(), tax1)
        
        user2_tax = TurnoverTaxRecord.objects.filter(user=self.user2)
        self.assertEqual(user2_tax.count(), 1)
        self.assertEqual(user2_tax.first(), tax2)
