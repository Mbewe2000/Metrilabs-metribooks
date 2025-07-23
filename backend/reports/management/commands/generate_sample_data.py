from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
import random

from sales.models import Sale
from services.models import ServiceCategory, Service, WorkRecord
from accounting.models import Expense, ExpenseCategory, IncomeRecord
from employees.models import Employee
from reports.models import ReportTemplate

User = get_user_model()


class Command(BaseCommand):
    help = 'Generate sample data for testing the reports module'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user-email',
            type=str,
            required=True,
            help='Email of the user to generate data for'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days of historical data to generate'
        )
        parser.add_argument(
            '--transactions-per-day',
            type=int,
            default=5,
            help='Average number of transactions per day'
        )
    
    def handle(self, *args, **options):
        """Generate sample data for reports testing"""
        
        try:
            user = User.objects.get(email=options['user_email'])
        except User.DoesNotExist:
            self.stderr.write(f'User with email {options["user_email"]} does not exist')
            return
        
        days = options['days']
        transactions_per_day = options['transactions_per_day']
        
        self.stdout.write(f'Generating {days} days of sample data for {user.email}...')
        
        # Generate sample data
        self.create_expense_categories(user)
        self.create_service_categories(user)
        self.create_services(user)
        self.create_employees(user)
        self.create_sample_transactions(user, days, transactions_per_day)
        self.create_sample_expenses(user, days)
        self.create_sample_service_records(user, days)
        self.create_sample_report_templates(user)
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully generated sample data for {user.email}')
        )
    
    def create_expense_categories(self, user):
        """Create sample expense categories"""
        categories = [
            'Office Supplies', 'Rent', 'Utilities', 'Marketing', 
            'Travel', 'Equipment', 'Professional Services', 'Insurance'
        ]
        
        for category_name in categories:
            ExpenseCategory.objects.get_or_create(
                user=user,
                name=category_name,
                defaults={'description': f'{category_name} expenses'}
            )
        
        self.stdout.write('  Created expense categories')
    
    def create_service_categories(self, user):
        """Create sample service categories"""
        categories = [
            ('Beauty Services', 'Hair, nails, and beauty treatments'),
            ('Cleaning Services', 'Professional cleaning services'),
            ('Consultation', 'Professional consultation services'),
            ('Delivery', 'Delivery and transportation services')
        ]
        
        for name, description in categories:
            ServiceCategory.objects.get_or_create(
                name=name,
                defaults={'description': description}
            )
        
        self.stdout.write('  Created service categories')
    
    def create_services(self, user):
        """Create sample services"""
        beauty_category = ServiceCategory.objects.get(name='Beauty Services')
        cleaning_category = ServiceCategory.objects.get(name='Cleaning Services')
        
        services = [
            ('Haircut', beauty_category, 'fixed', None, Decimal('50.00')),
            ('Hair Washing', beauty_category, 'hourly', Decimal('25.00'), None),
            ('Manicure', beauty_category, 'fixed', None, Decimal('30.00')),
            ('House Cleaning', cleaning_category, 'hourly', Decimal('40.00'), None),
            ('Office Cleaning', cleaning_category, 'hourly', Decimal('35.00'), None),
        ]
        
        for name, category, pricing_type, hourly_rate, fixed_price in services:
            Service.objects.get_or_create(
                user=user,
                name=name,
                category=category,
                defaults={
                    'pricing_type': pricing_type,
                    'hourly_rate': hourly_rate,
                    'fixed_price': fixed_price,
                    'description': f'{name} service'
                }
            )
        
        self.stdout.write('  Created services')
    
    def create_employees(self, user):
        """Create sample employees"""
        employees = [
            ('Alice Johnson', 'full_time', Decimal('15.00')),
            ('Bob Smith', 'part_time', Decimal('12.00')),
            ('Carol Brown', 'contract', Decimal('20.00')),
        ]
        
        for name, employment_type, hourly_rate in employees:
            first_name, last_name = name.split()
            Employee.objects.get_or_create(
                user=user,
                first_name=first_name,
                last_name=last_name,
                defaults={
                    'employment_type': employment_type,
                    'hourly_rate': hourly_rate,
                    'phone': f'+260977{random.randint(100000, 999999)}',
                    'position': 'Service Provider'
                }
            )
        
        self.stdout.write('  Created employees')
    
    def create_sample_transactions(self, user, days, transactions_per_day):
        """Create sample sales transactions"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        current_date = start_date
        total_transactions = 0
        
        while current_date <= end_date:
            # Generate random number of transactions for this day
            num_transactions = random.randint(
                max(1, transactions_per_day - 2), 
                transactions_per_day + 3
            )
            
            for _ in range(num_transactions):
                # Random sale amount between K20 and K500
                amount = Decimal(random.uniform(20.00, 500.00)).quantize(Decimal('0.01'))
                
                Sale.objects.create(
                    user=user,
                    sale_date=current_date,
                    total_amount=amount,
                    payment_method=random.choice(['cash', 'bank_transfer', 'mobile_money']),
                    notes=f'Sample sale transaction'
                )
                
                total_transactions += 1
            
            current_date += timedelta(days=1)
        
        self.stdout.write(f'  Created {total_transactions} sample sales transactions')
    
    def create_sample_expenses(self, user, days):
        """Create sample expense records"""
        expense_categories = ExpenseCategory.objects.filter(user=user)
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        current_date = start_date
        total_expenses = 0
        
        while current_date <= end_date:
            # Generate 1-3 expenses per day randomly
            if random.random() < 0.7:  # 70% chance of expenses on any given day
                num_expenses = random.randint(1, 3)
                
                for _ in range(num_expenses):
                    category = random.choice(expense_categories)
                    
                    # Random expense amount based on category
                    if category.name == 'Rent':
                        amount = Decimal(random.uniform(800.00, 1200.00))
                    elif category.name == 'Utilities':
                        amount = Decimal(random.uniform(100.00, 300.00))
                    elif category.name == 'Office Supplies':
                        amount = Decimal(random.uniform(20.00, 150.00))
                    else:
                        amount = Decimal(random.uniform(50.00, 400.00))
                    
                    amount = amount.quantize(Decimal('0.01'))
                    
                    Expense.objects.create(
                        user=user,
                        name=f'{category.name} expense',
                        amount=amount,
                        expense_date=current_date,
                        category=category,
                        expense_type='one_time',
                        notes='Sample expense record'
                    )
                    
                    total_expenses += 1
            
            current_date += timedelta(days=1)
        
        self.stdout.write(f'  Created {total_expenses} sample expense records')
    
    def create_sample_service_records(self, user, days):
        """Create sample service work records"""
        services = Service.objects.filter(user=user)
        employees = Employee.objects.filter(user=user)
        
        if not services.exists():
            return
        
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        current_date = start_date
        total_records = 0
        
        while current_date <= end_date:
            # Generate 0-3 service records per day
            if random.random() < 0.6:  # 60% chance of service work on any given day
                num_records = random.randint(1, 3)
                
                for _ in range(num_records):
                    service = random.choice(services)
                    
                    # Randomly assign to employee or owner
                    if employees.exists() and random.random() < 0.8:
                        # Employee work
                        employee = random.choice(employees)
                        worker_type = 'employee'
                        
                        if service.pricing_type == 'hourly':
                            hours_worked = Decimal(random.uniform(1.0, 8.0)).quantize(Decimal('0.25'))
                            total_amount = hours_worked * service.hourly_rate
                            quantity = 1
                        else:
                            hours_worked = None
                            quantity = random.randint(1, 3)
                            total_amount = quantity * service.fixed_price
                        
                        WorkRecord.objects.create(
                            worker_type=worker_type,
                            employee=employee,
                            service=service,
                            date_of_work=current_date,
                            hours_worked=hours_worked,
                            quantity=quantity,
                            total_amount=total_amount,
                            notes='Sample service work record'
                        )
                    else:
                        # Owner work
                        worker_type = 'owner'
                        owner_name = 'Business Owner'
                        
                        if service.pricing_type == 'hourly':
                            hours_worked = Decimal(random.uniform(1.0, 6.0)).quantize(Decimal('0.25'))
                            total_amount = hours_worked * service.hourly_rate
                            quantity = 1
                        else:
                            hours_worked = None
                            quantity = random.randint(1, 2)
                            total_amount = quantity * service.fixed_price
                        
                        WorkRecord.objects.create(
                            worker_type=worker_type,
                            owner_name=owner_name,
                            service=service,
                            date_of_work=current_date,
                            hours_worked=hours_worked,
                            quantity=quantity,
                            total_amount=total_amount,
                            notes='Sample owner work record'
                        )
                    
                    total_records += 1
            
            current_date += timedelta(days=1)
        
        self.stdout.write(f'  Created {total_records} sample service work records')
    
    def create_sample_report_templates(self, user):
        """Create sample report templates"""
        templates = [
            {
                'name': 'Monthly Business Summary',
                'description': 'Comprehensive monthly business analysis',
                'report_types': ['profit_loss', 'cash_flow', 'tax_summary'],
                'frequency': 'monthly',
                'auto_generate': True
            },
            {
                'name': 'Weekly Performance Review',
                'description': 'Weekly sales and service performance',
                'report_types': ['sales_trend', 'business_overview'],
                'frequency': 'weekly',
                'auto_generate': False
            },
            {
                'name': 'Tax Compliance Report',
                'description': 'Monthly tax calculation and compliance',
                'report_types': ['tax_summary'],
                'frequency': 'monthly',
                'auto_generate': True
            }
        ]
        
        for template_data in templates:
            ReportTemplate.objects.get_or_create(
                user=user,
                name=template_data['name'],
                defaults=template_data
            )
        
        self.stdout.write('  Created sample report templates')
