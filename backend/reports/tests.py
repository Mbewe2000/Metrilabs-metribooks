from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from decimal import Decimal
from datetime import date, timedelta
import json

from .models import ReportSnapshot, ReportTemplate, BusinessMetric
from .utils import ReportGenerator, ReportCache
from sales.models import Sale
from services.models import ServiceCategory, Service, WorkRecord
from accounting.models import Expense, ExpenseCategory, IncomeRecord
from employees.models import Employee

User = get_user_model()


class ReportModelsTestCase(TestCase):
    """Test cases for Reports models"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_report_snapshot_creation(self):
        """Test creating a report snapshot"""
        snapshot = ReportSnapshot.objects.create(
            user=self.user,
            report_type='profit_loss',
            period_start=date(2025, 1, 1),
            period_end=date(2025, 1, 31),
            total_income=Decimal('5000.00'),
            total_expenses=Decimal('3000.00'),
            net_profit=Decimal('2000.00')
        )
        
        self.assertEqual(snapshot.user, self.user)
        self.assertEqual(snapshot.report_type, 'profit_loss')
        self.assertEqual(snapshot.get_profit_margin_percentage(), Decimal('40.00'))
        self.assertEqual(snapshot.get_expense_ratio_percentage(), Decimal('60.00'))
    
    def test_report_template_creation(self):
        """Test creating a report template"""
        template = ReportTemplate.objects.create(
            user=self.user,
            name='Monthly Summary',
            description='Monthly profit and cash flow summary',
            report_types=['profit_loss', 'cash_flow'],
            frequency='monthly',
            auto_generate=True
        )
        
        self.assertEqual(template.user, self.user)
        self.assertEqual(template.name, 'Monthly Summary')
        self.assertTrue(template.auto_generate)
    
    def test_business_metric_creation(self):
        """Test creating business metrics"""
        metric = BusinessMetric.objects.create(
            user=self.user,
            metric_type='revenue_growth',
            metric_date=date.today(),
            value=Decimal('5000.00'),
            percentage_value=Decimal('15.50'),
            previous_period_value=Decimal('4347.83'),
            change_percentage=Decimal('15.00')
        )
        
        self.assertEqual(metric.user, self.user)
        self.assertEqual(metric.get_trend_direction(), 'up')
        self.assertTrue(metric.is_positive_change())


class ReportGeneratorTestCase(TestCase):
    """Test cases for ReportGenerator utility"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test data for reports
        self.expense_category = ExpenseCategory.objects.create(
            name='operational',
            description='Office Supplies'
        )
        
        # Create some sales
        Sale.objects.create(
            user=self.user,
            sale_date=date.today(),
            subtotal=Decimal('1500.00'),
            total_amount=Decimal('1500.00'),
            payment_method='cash'
        )
        
        # Create some expenses
        Expense.objects.create(
            user=self.user,
            name='Office Rent',
            amount=Decimal('800.00'),
            expense_date=date.today(),
            category=self.expense_category
        )
        
        self.generator = ReportGenerator(self.user)
    
    def test_profit_loss_report_generation(self):
        """Test profit & loss report generation"""
        today = date.today()
        report = self.generator.generate_profit_loss_report(today, today)
        
        self.assertIn('period_start', report)
        self.assertIn('period_end', report)
        self.assertIn('total_income', report)
        self.assertIn('total_expenses', report)
        self.assertIn('net_profit', report)
        
        # Check if our test data is reflected
        self.assertEqual(report['sales_revenue'], Decimal('1500.00'))
        self.assertEqual(report['operating_expenses'], Decimal('800.00'))
        self.assertEqual(report['net_profit'], Decimal('700.00'))  # Sales - Expenses
    
    def test_cash_flow_report_generation(self):
        """Test cash flow report generation"""
        today = date.today()
        report = self.generator.generate_cash_flow_report(today, today)
        
        self.assertIn('period_start', report)
        self.assertIn('period_end', report)
        self.assertIn('total_cash_inflows', report)
        self.assertIn('total_cash_outflows', report)
        self.assertIn('net_cash_flow', report)
        
        # Check calculated values
        self.assertEqual(report['cash_from_sales'], Decimal('1500.00'))
        self.assertEqual(report['cash_for_expenses'], Decimal('800.00'))
    
    def test_tax_summary_report_generation(self):
        """Test tax summary report generation"""
        today = date.today()
        report = self.generator.generate_tax_summary_report(today, today)
        
        self.assertIn('total_revenue', report)
        self.assertIn('taxable_income', report)
        self.assertIn('turnover_tax_due', report)
        self.assertIn('monthly_breakdown', report)
        
        # Check ZRA tax calculation
        expected_taxable = max(Decimal('1500.00') - Decimal('1000.00'), Decimal('0.00'))
        expected_tax = expected_taxable * Decimal('5.00') / 100
        
        monthly_data = report['monthly_breakdown'][0]  # Current month
        self.assertEqual(monthly_data['taxable_income'], expected_taxable)
        self.assertEqual(monthly_data['tax_due'], expected_tax)


class ReportAPITestCase(APITestCase):
    """Test cases for Reports API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        # Create some test data
        Sale.objects.create(
            user=self.user,
            sale_date=date.today(),
            subtotal=Decimal('2000.00'),
            total_amount=Decimal('2000.00'),
            payment_method='cash'
        )
        
        self.client.force_authenticate(user=self.user)
    
    def test_profit_loss_summary_endpoint(self):
        """Test profit & loss summary API endpoint"""
        url = '/api/reports/profit-loss/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertIn('total_income', data)
        self.assertIn('total_expenses', data)
        self.assertIn('net_profit', data)
        self.assertIn('period_start', data)
        self.assertIn('period_end', data)
    
    def test_cash_flow_summary_endpoint(self):
        """Test cash flow summary API endpoint"""
        url = '/api/reports/cash-flow/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertIn('total_cash_inflows', data)
        self.assertIn('total_cash_outflows', data)
        self.assertIn('net_cash_flow', data)
    
    def test_tax_summary_endpoint(self):
        """Test tax summary API endpoint"""
        url = '/api/reports/tax-summary/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertIn('total_revenue', data)
        self.assertIn('turnover_tax_due', data)
        self.assertIn('monthly_breakdown', data)
        self.assertIn('is_eligible_for_turnover_tax', data)
    
    def test_business_overview_endpoint(self):
        """Test business overview API endpoint"""
        url = '/api/reports/business-overview/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertIn('total_revenue', data)
        self.assertIn('net_profit', data)
        self.assertIn('profit_margin', data)
        self.assertIn('total_sales_transactions', data)
    
    def test_analytics_dashboard_endpoint(self):
        """Test analytics dashboard API endpoint"""
        url = '/api/reports/dashboard/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertIn('current_month', data)
        self.assertIn('growth_metrics', data)
        self.assertIn('latest_business_metrics', data)
        self.assertIn('sales_trend_6months', data)
    
    def test_report_generation_endpoint(self):
        """Test report generation API endpoint"""
        url = '/api/reports/generate/'
        payload = {
            'report_type': 'profit_loss',
            'period_start': '2025-07-01',
            'period_end': '2025-07-23',
            'force_regenerate': False
        }
        
        response = self.client.post(url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertIn('report_type', data)
        self.assertIn('data', data)
        self.assertIn('generated_at', data)
        self.assertEqual(data['report_type'], 'profit_loss')
    
    def test_custom_date_range_filtering(self):
        """Test API endpoints with custom date range"""
        url = '/api/reports/profit-loss/'
        params = {
            'start_date': '2025-07-01',
            'end_date': '2025-07-23'
        }
        
        response = self.client.get(url, params)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data['period_start'], '2025-07-01')
        self.assertEqual(data['period_end'], '2025-07-23')
    
    def test_unauthenticated_access(self):
        """Test that unauthenticated users cannot access reports"""
        self.client.force_authenticate(user=None)
        
        url = '/api/reports/profit-loss/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ReportTemplateAPITestCase(APITestCase):
    """Test cases for Report Template API"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.template_data = {
            'name': 'Monthly Business Report',
            'description': 'Comprehensive monthly business analysis',
            'report_types': ['profit_loss', 'cash_flow', 'tax_summary'],
            'frequency': 'monthly',
            'auto_generate': True,
            'include_sales': True,
            'include_services': True,
            'include_expenses': True,
            'email_recipients': ['owner@business.com']
        }
    
    def test_create_report_template(self):
        """Test creating a report template via API"""
        url = '/api/reports/templates/'
        response = self.client.post(url, self.template_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        
        self.assertEqual(data['name'], 'Monthly Business Report')
        self.assertEqual(data['frequency'], 'monthly')
        self.assertTrue(data['auto_generate'])
        self.assertEqual(len(data['report_types']), 3)
    
    def test_list_report_templates(self):
        """Test listing report templates"""
        # Create a template first
        ReportTemplate.objects.create(
            user=self.user,
            **self.template_data
        )
        
        url = '/api/reports/templates/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertGreater(len(data), 0)
        self.assertEqual(data[0]['name'], 'Monthly Business Report')
    
    def test_generate_from_template(self):
        """Test generating reports from a template"""
        template = ReportTemplate.objects.create(
            user=self.user,
            **self.template_data
        )
        
        url = f'/api/reports/templates/{template.id}/generate_from_template/'
        payload = {
            'period_start': '2025-07-01',
            'period_end': '2025-07-23'
        }
        
        response = self.client.post(url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertIn('template_name', data)
        self.assertIn('reports', data)
        self.assertEqual(len(data['reports']), 3)  # profit_loss, cash_flow, tax_summary


class BusinessMetricAPITestCase(APITestCase):
    """Test cases for Business Metric API"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create some test metrics
        BusinessMetric.objects.create(
            user=self.user,
            metric_type='revenue_growth',
            metric_date=date.today(),
            value=Decimal('5000.00'),
            percentage_value=Decimal('12.50'),
            change_percentage=Decimal('12.50')
        )
    
    def test_list_business_metrics(self):
        """Test listing business metrics"""
        url = '/api/reports/metrics/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertGreater(len(data), 0)
        self.assertEqual(data[0]['metric_type'], 'revenue_growth')
    
    def test_latest_metrics_endpoint(self):
        """Test latest metrics endpoint"""
        url = '/api/reports/metrics/latest_metrics/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should return list of latest metrics
        self.assertIsInstance(data, list)
    
    def test_metric_trends_endpoint(self):
        """Test metric trends endpoint"""
        url = '/api/reports/metrics/metric_trends/'
        params = {'metric_type': 'revenue_growth'}
        
        response = self.client.get(url, params)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertIn('metric_type', data)
        self.assertIn('trend_data', data)
        self.assertEqual(data['metric_type'], 'revenue_growth')


class ReportCacheTestCase(TestCase):
    """Test cases for report caching functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_cache_report(self):
        """Test caching a report"""
        report_data = {
            'total_income': Decimal('5000.00'),
            'total_expenses': Decimal('3000.00'),
            'net_profit': Decimal('2000.00'),
            'sales_revenue': Decimal('4500.00'),
            'number_of_transactions': 25
        }
        
        snapshot = ReportCache.cache_report(
            self.user, 'profit_loss', date(2025, 7, 1), date(2025, 7, 23), report_data
        )
        
        self.assertEqual(snapshot.user, self.user)
        self.assertEqual(snapshot.report_type, 'profit_loss')
        self.assertEqual(snapshot.total_income, Decimal('5000.00'))
        self.assertTrue(snapshot.is_cached)
    
    def test_get_cached_report(self):
        """Test retrieving a cached report"""
        # First cache a report
        ReportSnapshot.objects.create(
            user=self.user,
            report_type='profit_loss',
            period_start=date(2025, 7, 1),
            period_end=date(2025, 7, 23),
            total_income=Decimal('5000.00'),
            is_cached=True
        )
        
        # Try to retrieve it
        cached_report = ReportCache.get_cached_report(
            self.user, 'profit_loss', date(2025, 7, 1), date(2025, 7, 23)
        )
        
        self.assertIsNotNone(cached_report)
        self.assertEqual(cached_report.total_income, Decimal('5000.00'))
    
    def test_get_cached_report_not_found(self):
        """Test retrieving a non-existent cached report"""
        cached_report = ReportCache.get_cached_report(
            self.user, 'profit_loss', date(2025, 1, 1), date(2025, 1, 31)
        )
        
        self.assertIsNone(cached_report)
