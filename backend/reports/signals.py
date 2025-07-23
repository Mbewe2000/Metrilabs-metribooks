from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta

# Import models from other apps for signal listening
from sales.models import Sale, SaleItem
from services.models import WorkRecord
from accounting.models import Expense, IncomeRecord, TurnoverTaxRecord
from inventory.models import StockMovement

from .models import ReportSnapshot, BusinessMetric


@receiver(post_save, sender=Sale)
def update_reports_on_sale_creation(sender, instance, created, **kwargs):
    """
    Update report snapshots when a new sale is created
    """
    if created:
        # Trigger report update for the current month
        current_month_start = date.today().replace(day=1)
        current_month_end = (current_month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        # Update business metrics
        _update_sales_metrics(instance.user, current_month_start, current_month_end)


@receiver(post_save, sender=WorkRecord)
def update_reports_on_work_record_creation(sender, instance, created, **kwargs):
    """
    Update report snapshots when a new work record is created
    """
    if created:
        # Get the user from the work record
        user = instance.service.user if hasattr(instance.service, 'user') else None
        if user:
            current_month_start = date.today().replace(day=1)
            current_month_end = (current_month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            # Update service metrics
            _update_service_metrics(user, current_month_start, current_month_end)


@receiver(post_save, sender=Expense)
def update_reports_on_expense_creation(sender, instance, created, **kwargs):
    """
    Update report snapshots when a new expense is created
    """
    if created:
        current_month_start = date.today().replace(day=1)
        current_month_end = (current_month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        # Update expense metrics
        _update_expense_metrics(instance.user, current_month_start, current_month_end)


@receiver(post_save, sender=IncomeRecord)
def update_reports_on_income_creation(sender, instance, created, **kwargs):
    """
    Update report snapshots when income is recorded
    """
    if created:
        current_month_start = date.today().replace(day=1)
        current_month_end = (current_month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        # Update income metrics
        _update_income_metrics(instance.user, current_month_start, current_month_end)


def _update_sales_metrics(user, period_start, period_end):
    """Update sales-related business metrics"""
    try:
        from sales.models import Sale
        from django.db.models import Sum, Count, Avg
        
        # Calculate current period metrics
        sales_data = Sale.objects.filter(
            user=user,
            sale_date__range=[period_start, period_end]
        ).aggregate(
            total_sales=Sum('total_amount'),
            sales_count=Count('id'),
            avg_sale=Avg('total_amount')
        )
        
        total_sales = sales_data['total_sales'] or Decimal('0.00')
        sales_count = sales_data['sales_count'] or 0
        avg_sale = sales_data['avg_sale'] or Decimal('0.00')
        
        # Calculate previous period for comparison
        prev_period_start = period_start - timedelta(days=(period_end - period_start).days + 1)
        prev_period_end = period_start - timedelta(days=1)
        
        prev_sales_data = Sale.objects.filter(
            user=user,
            sale_date__range=[prev_period_start, prev_period_end]
        ).aggregate(
            total_sales=Sum('total_amount')
        )
        
        prev_total_sales = prev_sales_data['total_sales'] or Decimal('0.00')
        
        # Calculate growth rate
        growth_rate = Decimal('0.00')
        if prev_total_sales > 0:
            growth_rate = ((total_sales - prev_total_sales) / prev_total_sales) * 100
        
        # Update or create business metrics
        BusinessMetric.objects.update_or_create(
            user=user,
            metric_type='revenue_growth',
            metric_date=period_end,
            defaults={
                'value': total_sales,
                'percentage_value': growth_rate,
                'previous_period_value': prev_total_sales,
                'change_percentage': growth_rate,
                'metadata': {
                    'sales_count': sales_count,
                    'average_sale_value': str(avg_sale),
                    'period_start': str(period_start),
                    'period_end': str(period_end)
                }
            }
        )
        
        # Update average order value metric
        BusinessMetric.objects.update_or_create(
            user=user,
            metric_type='average_order_value',
            metric_date=period_end,
            defaults={
                'value': avg_sale,
                'metadata': {
                    'total_sales': str(total_sales),
                    'sales_count': sales_count
                }
            }
        )
        
    except Exception as e:
        # Log error but don't break the signal
        import logging
        logger = logging.getLogger('reports')
        logger.error(f"Error updating sales metrics: {str(e)}")


def _update_service_metrics(user, period_start, period_end):
    """Update service-related business metrics"""
    try:
        from services.models import WorkRecord
        from django.db.models import Sum, Count
        
        # Calculate service metrics
        service_data = WorkRecord.objects.filter(
            service__user=user,
            date_of_work__range=[period_start, period_end]
        ).aggregate(
            total_hours=Sum('hours_worked'),
            total_revenue=Sum('total_amount'),
            record_count=Count('id')
        )
        
        total_hours = service_data['total_hours'] or Decimal('0.00')
        total_revenue = service_data['total_revenue'] or Decimal('0.00')
        record_count = service_data['record_count'] or 0
        
        # Calculate utilization rate (assuming 8 hours per day as full utilization)
        days_in_period = (period_end - period_start).days + 1
        max_possible_hours = days_in_period * 8
        utilization_rate = (total_hours / max_possible_hours * 100) if max_possible_hours > 0 else Decimal('0.00')
        
        BusinessMetric.objects.update_or_create(
            user=user,
            metric_type='service_utilization',
            metric_date=period_end,
            defaults={
                'value': total_hours,
                'percentage_value': utilization_rate,
                'metadata': {
                    'total_revenue': str(total_revenue),
                    'record_count': record_count,
                    'days_in_period': days_in_period,
                    'utilization_rate': str(utilization_rate)
                }
            }
        )
        
    except Exception as e:
        import logging
        logger = logging.getLogger('reports')
        logger.error(f"Error updating service metrics: {str(e)}")


def _update_expense_metrics(user, period_start, period_end):
    """Update expense-related business metrics"""
    try:
        from accounting.models import Expense, IncomeRecord
        from django.db.models import Sum
        
        # Calculate expenses
        total_expenses = Expense.objects.filter(
            user=user,
            expense_date__range=[period_start, period_end]
        ).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        # Calculate income for the same period
        total_income = IncomeRecord.objects.filter(
            user=user,
            income_date__range=[period_start, period_end]
        ).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
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
        
    except Exception as e:
        import logging
        logger = logging.getLogger('reports')
        logger.error(f"Error updating expense metrics: {str(e)}")


def _update_income_metrics(user, period_start, period_end):
    """Update income-related business metrics"""
    try:
        from accounting.models import IncomeRecord, Expense
        from django.db.models import Sum
        
        # Calculate total income
        total_income = IncomeRecord.objects.filter(
            user=user,
            income_date__range=[period_start, period_end]
        ).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        # Calculate total expenses
        total_expenses = Expense.objects.filter(
            user=user,
            expense_date__range=[period_start, period_end]
        ).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
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
                    'total_expenses': str(total_expenses),
                    'profit_margin': str(profit_margin)
                }
            }
        )
        
    except Exception as e:
        import logging
        logger = logging.getLogger('reports')
        logger.error(f"Error updating income metrics: {str(e)}")


# Signal to update report snapshots when significant data changes
@receiver([post_save, post_delete], sender=Sale)
@receiver([post_save, post_delete], sender=WorkRecord)
@receiver([post_save, post_delete], sender=Expense)
@receiver([post_save, post_delete], sender=IncomeRecord)
def invalidate_report_cache(sender, instance, **kwargs):
    """
    Invalidate cached report snapshots when data changes
    """
    try:
        # Get user from instance
        user = None
        if hasattr(instance, 'user'):
            user = instance.user
        elif hasattr(instance, 'service') and hasattr(instance.service, 'user'):
            user = instance.service.user
        
        if user:
            # Mark relevant report snapshots as stale
            current_date = timezone.now().date()
            ReportSnapshot.objects.filter(
                user=user,
                period_end__gte=current_date - timedelta(days=30),
                is_cached=True
            ).update(is_cached=False)
            
    except Exception as e:
        import logging
        logger = logging.getLogger('reports')
        logger.error(f"Error invalidating report cache: {str(e)}")
