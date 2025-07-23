from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

from reports.models import ReportTemplate, BusinessMetric
from reports.utils import ReportGenerator, ReportCache

User = get_user_model()


class Command(BaseCommand):
    help = 'Generate reports and update business metrics for automated reporting'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user-email',
            type=str,
            help='Generate reports for specific user email'
        )
        parser.add_argument(
            '--template-id',
            type=str,
            help='Generate reports from specific template ID'
        )
        parser.add_argument(
            '--period-start',
            type=str,
            help='Start date for reporting period (YYYY-MM-DD)'
        )
        parser.add_argument(
            '--period-end',
            type=str,
            help='End date for reporting period (YYYY-MM-DD)'
        )
        parser.add_argument(
            '--auto-templates',
            action='store_true',
            help='Process all auto-generate templates'
        )
        parser.add_argument(
            '--update-metrics',
            action='store_true',
            help='Update business metrics for all users'
        )
        parser.add_argument(
            '--force-regenerate',
            action='store_true',
            help='Force regenerate reports even if cached'
        )
    
    def handle(self, *args, **options):
        """Handle the management command"""
        
        if options['auto_templates']:
            self.process_auto_templates()
        
        if options['update_metrics']:
            self.update_business_metrics()
        
        if options['user_email'] and options['template_id']:
            self.generate_template_reports(
                options['user_email'],
                options['template_id'],
                options.get('period_start'),
                options.get('period_end'),
                options.get('force_regenerate', False)
            )
        elif options['user_email']:
            self.generate_user_reports(
                options['user_email'],
                options.get('period_start'),
                options.get('period_end'),
                options.get('force_regenerate', False)
            )
    
    def process_auto_templates(self):
        """Process all templates with auto_generate enabled"""
        self.stdout.write('Processing auto-generate templates...')
        
        auto_templates = ReportTemplate.objects.filter(
            auto_generate=True,
            is_active=True
        )
        
        processed_count = 0
        
        for template in auto_templates:
            try:
                # Determine period based on template frequency
                period_start, period_end = self.get_period_for_frequency(template.frequency)
                
                # Generate reports for this template
                self.generate_template_reports(
                    template.user.email,
                    str(template.id),
                    period_start.isoformat(),
                    period_end.isoformat(),
                    False
                )
                
                processed_count += 1
                
            except Exception as e:
                self.stderr.write(
                    f'Error processing template {template.name} for user {template.user.email}: {str(e)}'
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Processed {processed_count} auto-generate templates')
        )
    
    def update_business_metrics(self):
        """Update business metrics for all users"""
        self.stdout.write('Updating business metrics...')
        
        users = User.objects.all()
        updated_count = 0
        
        today = date.today()
        current_month_start = today.replace(day=1)
        
        for user in users:
            try:
                # Update metrics for current month
                self.update_user_metrics(user, current_month_start, today)
                updated_count += 1
                
            except Exception as e:
                self.stderr.write(
                    f'Error updating metrics for user {user.email}: {str(e)}'
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Updated business metrics for {updated_count} users')
        )
    
    def generate_template_reports(self, user_email, template_id, period_start=None, period_end=None, force_regenerate=False):
        """Generate reports from a specific template"""
        try:
            user = User.objects.get(email=user_email)
            template = ReportTemplate.objects.get(id=template_id, user=user)
            
        except User.DoesNotExist:
            raise CommandError(f'User with email {user_email} does not exist')
        except ReportTemplate.DoesNotExist:
            raise CommandError(f'Template with ID {template_id} not found for user {user_email}')
        
        # Determine period
        if period_start and period_end:
            period_start = date.fromisoformat(period_start)
            period_end = date.fromisoformat(period_end)
        else:
            period_start, period_end = self.get_period_for_frequency(template.frequency)
        
        self.stdout.write(
            f'Generating reports from template "{template.name}" for user {user_email}...'
        )
        
        generator = ReportGenerator(user)
        generated_reports = []
        
        for report_type in template.report_types:
            try:
                # Check for cached report if not forcing regeneration
                if not force_regenerate:
                    cached_report = ReportCache.get_cached_report(
                        user, report_type, period_start, period_end
                    )
                    if cached_report:
                        self.stdout.write(f'  Using cached {report_type} report')
                        continue
                
                # Generate the report
                if report_type == 'profit_loss':
                    report_data = generator.generate_profit_loss_report(period_start, period_end)
                elif report_type == 'cash_flow':
                    report_data = generator.generate_cash_flow_report(period_start, period_end)
                elif report_type == 'sales_trend':
                    report_data = generator.generate_sales_trend_report(period_start, period_end)
                elif report_type == 'expense_trend':
                    report_data = generator.generate_expense_trend_report(period_start, period_end)
                elif report_type == 'tax_summary':
                    report_data = generator.generate_tax_summary_report(period_start, period_end)
                elif report_type == 'business_overview':
                    report_data = generator.generate_business_overview_report(period_start, period_end)
                else:
                    self.stderr.write(f'  Unsupported report type: {report_type}')
                    continue
                
                # Cache the report
                ReportCache.cache_report(user, report_type, period_start, period_end, report_data)
                generated_reports.append(report_type)
                
                self.stdout.write(f'  Generated {report_type} report')
                
            except Exception as e:
                self.stderr.write(f'  Error generating {report_type} report: {str(e)}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Generated {len(generated_reports)} reports from template "{template.name}"'
            )
        )
    
    def generate_user_reports(self, user_email, period_start=None, period_end=None, force_regenerate=False):
        """Generate all standard reports for a user"""
        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            raise CommandError(f'User with email {user_email} does not exist')
        
        # Default to current month
        if not period_start or not period_end:
            today = date.today()
            period_start = today.replace(day=1)
            period_end = today
        else:
            period_start = date.fromisoformat(period_start)
            period_end = date.fromisoformat(period_end)
        
        self.stdout.write(f'Generating reports for user {user_email}...')
        
        generator = ReportGenerator(user)
        report_types = ['profit_loss', 'cash_flow', 'tax_summary', 'business_overview']
        generated_count = 0
        
        for report_type in report_types:
            try:
                # Check for cached report if not forcing regeneration
                if not force_regenerate:
                    cached_report = ReportCache.get_cached_report(
                        user, report_type, period_start, period_end
                    )
                    if cached_report:
                        self.stdout.write(f'  Using cached {report_type} report')
                        continue
                
                # Generate the report based on type
                if report_type == 'profit_loss':
                    report_data = generator.generate_profit_loss_report(period_start, period_end)
                elif report_type == 'cash_flow':
                    report_data = generator.generate_cash_flow_report(period_start, period_end)
                elif report_type == 'tax_summary':
                    report_data = generator.generate_tax_summary_report(period_start, period_end)
                elif report_type == 'business_overview':
                    report_data = generator.generate_business_overview_report(period_start, period_end)
                
                # Cache the report
                ReportCache.cache_report(user, report_type, period_start, period_end, report_data)
                generated_count += 1
                
                self.stdout.write(f'  Generated {report_type} report')
                
            except Exception as e:
                self.stderr.write(f'  Error generating {report_type} report: {str(e)}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Generated {generated_count} reports for user {user_email}')
        )
    
    def update_user_metrics(self, user, period_start, period_end):
        """Update business metrics for a specific user"""
        from sales.models import Sale
        from services.models import WorkRecord
        from accounting.models import Expense, IncomeRecord
        from django.db.models import Sum, Count, Avg
        
        # Calculate revenue growth
        current_revenue = Sale.objects.filter(
            user=user,
            sale_date__range=[period_start, period_end]
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        
        # Previous period for comparison
        prev_period_start = period_start - timedelta(days=(period_end - period_start).days + 1)
        prev_period_end = period_start - timedelta(days=1)
        
        prev_revenue = Sale.objects.filter(
            user=user,
            sale_date__range=[prev_period_start, prev_period_end]
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        
        # Calculate growth rate
        revenue_growth = Decimal('0.00')
        if prev_revenue > 0:
            revenue_growth = ((current_revenue - prev_revenue) / prev_revenue) * 100
        
        # Update revenue growth metric
        BusinessMetric.objects.update_or_create(
            user=user,
            metric_type='revenue_growth',
            metric_date=period_end,
            defaults={
                'value': current_revenue,
                'percentage_value': revenue_growth,
                'previous_period_value': prev_revenue,
                'change_percentage': revenue_growth
            }
        )
        
        # Calculate and update other metrics...
        self.update_profit_margin_metric(user, period_start, period_end)
        self.update_expense_ratio_metric(user, period_start, period_end)
        self.update_average_order_value_metric(user, period_start, period_end)
    
    def update_profit_margin_metric(self, user, period_start, period_end):
        """Update profit margin metric"""
        from sales.models import Sale
        from services.models import WorkRecord
        from accounting.models import Expense, IncomeRecord
        from django.db.models import Sum
        
        # Calculate total income
        sales_income = Sale.objects.filter(
            user=user,
            sale_date__range=[period_start, period_end]
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        
        service_income = WorkRecord.objects.filter(
            service__user=user,
            date_of_work__range=[period_start, period_end]
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        
        other_income = IncomeRecord.objects.filter(
            user=user,
            source='other',
            income_date__range=[period_start, period_end]
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        total_income = sales_income + service_income + other_income
        
        # Calculate total expenses
        total_expenses = Expense.objects.filter(
            user=user,
            expense_date__range=[period_start, period_end]
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Calculate profit margin
        net_profit = total_income - total_expenses
        profit_margin = (net_profit / total_income * 100) if total_income > 0 else Decimal('0.00')
        
        BusinessMetric.objects.update_or_create(
            user=user,
            metric_type='profit_margin',
            metric_date=period_end,
            defaults={
                'value': net_profit,
                'percentage_value': profit_margin,
                'metadata': {
                    'total_income': str(total_income),
                    'total_expenses': str(total_expenses)
                }
            }
        )
    
    def update_expense_ratio_metric(self, user, period_start, period_end):
        """Update expense ratio metric"""
        from sales.models import Sale
        from accounting.models import Expense, IncomeRecord
        from django.db.models import Sum
        
        # Calculate total income and expenses
        total_income = Sale.objects.filter(
            user=user,
            sale_date__range=[period_start, period_end]
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        
        total_expenses = Expense.objects.filter(
            user=user,
            expense_date__range=[period_start, period_end]
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Calculate expense ratio
        expense_ratio = (total_expenses / total_income * 100) if total_income > 0 else Decimal('0.00')
        
        BusinessMetric.objects.update_or_create(
            user=user,
            metric_type='expense_ratio',
            metric_date=period_end,
            defaults={
                'value': total_expenses,
                'percentage_value': expense_ratio,
                'metadata': {
                    'total_income': str(total_income),
                    'expense_ratio': str(expense_ratio)
                }
            }
        )
    
    def update_average_order_value_metric(self, user, period_start, period_end):
        """Update average order value metric"""
        from sales.models import Sale
        from django.db.models import Sum, Count, Avg
        
        # Calculate average order value
        sales_data = Sale.objects.filter(
            user=user,
            sale_date__range=[period_start, period_end]
        ).aggregate(
            total_sales=Sum('total_amount'),
            sales_count=Count('id'),
            avg_sale=Avg('total_amount')
        )
        
        avg_order_value = sales_data['avg_sale'] or Decimal('0.00')
        
        BusinessMetric.objects.update_or_create(
            user=user,
            metric_type='average_order_value',
            metric_date=period_end,
            defaults={
                'value': avg_order_value,
                'metadata': {
                    'total_sales': str(sales_data['total_sales'] or Decimal('0.00')),
                    'sales_count': sales_data['sales_count'] or 0
                }
            }
        )
    
    def get_period_for_frequency(self, frequency):
        """Get appropriate period dates based on frequency"""
        today = date.today()
        
        if frequency == 'daily':
            return today, today
        elif frequency == 'weekly':
            start = today - timedelta(days=today.weekday())
            end = start + timedelta(days=6)
            return start, min(end, today)
        elif frequency == 'monthly':
            start = today.replace(day=1)
            return start, today
        elif frequency == 'quarterly':
            # Get current quarter
            quarter = (today.month - 1) // 3 + 1
            start = date(today.year, 3 * quarter - 2, 1)
            return start, today
        elif frequency == 'yearly':
            start = date(today.year, 1, 1)
            return start, today
        else:  # custom or default to monthly
            start = today.replace(day=1)
            return start, today
