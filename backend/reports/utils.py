from django.db.models import Q, Sum, Count, Avg, F, Case, When, DecimalField
from django.utils import timezone
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
import logging
import json

from .models import ReportSnapshot, BusinessMetric

logger = logging.getLogger('reports')


class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle Decimal objects"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)


class ReportGenerator:
    """
    Utility class for generating comprehensive business reports
    """
    
    def __init__(self, user):
        self.user = user
    
    def generate_profit_loss_report(self, period_start: date, period_end: date) -> Dict:
        """
        Generate a comprehensive Profit & Loss report
        """
        try:
            from sales.models import Sale
            from services.models import WorkRecord
            from accounting.models import Expense, IncomeRecord
            
            # Calculate income sources
            sales_revenue = Sale.objects.filter(
                user=self.user,
                sale_date__range=[period_start, period_end]
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            
            service_revenue = WorkRecord.objects.filter(
                user=self.user,
                date_of_work__range=[period_start, period_end]
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            
            other_income = IncomeRecord.objects.filter(
                user=self.user,
                source='other',
                income_date__range=[period_start, period_end]
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            total_income = sales_revenue + service_revenue + other_income
            
            # Calculate expenses by category
            expense_data = Expense.objects.filter(
                user=self.user,
                expense_date__range=[period_start, period_end]
            ).values('category__name').annotate(
                total=Sum('amount')
            ).order_by('-total')
            
            total_expenses = Expense.objects.filter(
                user=self.user,
                expense_date__range=[period_start, period_end]
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            # Calculate profit metrics
            gross_profit = total_income - total_expenses
            net_profit = gross_profit  # Simplified for this implementation
            
            # Calculate percentages
            gross_margin_percentage = (gross_profit / total_income * 100) if total_income > 0 else Decimal('0.00')
            net_margin_percentage = (net_profit / total_income * 100) if total_income > 0 else Decimal('0.00')
            
            # Count transactions
            number_of_transactions = Sale.objects.filter(
                user=self.user,
                sale_date__range=[period_start, period_end]
            ).count()
            
            average_transaction_value = (total_income / number_of_transactions) if number_of_transactions > 0 else Decimal('0.00')
            
            return {
                'period_start': period_start,
                'period_end': period_end,
                'sales_revenue': sales_revenue,
                'service_revenue': service_revenue,
                'other_income': other_income,
                'total_income': total_income,
                'cost_of_goods_sold': Decimal('0.00'),  # To be implemented based on business needs
                'operating_expenses': total_expenses,
                'administrative_expenses': Decimal('0.00'),  # Can be categorized further
                'total_expenses': total_expenses,
                'gross_profit': gross_profit,
                'net_profit': net_profit,
                'gross_margin_percentage': gross_margin_percentage,
                'net_margin_percentage': net_margin_percentage,
                'number_of_transactions': number_of_transactions,
                'average_transaction_value': average_transaction_value,
                'expense_breakdown': list(expense_data)
            }
            
        except Exception as e:
            logger.error(f"Error generating profit/loss report: {str(e)}")
            raise
    
    def generate_cash_flow_report(self, period_start: date, period_end: date) -> Dict:
        """
        Generate a Cash Flow report
        """
        try:
            from sales.models import Sale
            from services.models import WorkRecord
            from accounting.models import Expense, Asset, IncomeRecord
            
            # Cash inflows
            cash_from_sales = Sale.objects.filter(
                user=self.user,
                sale_date__range=[period_start, period_end]
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            
            cash_from_services = WorkRecord.objects.filter(
                user=self.user,
                date_of_work__range=[period_start, period_end]
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            
            other_cash_inflows = IncomeRecord.objects.filter(
                user=self.user,
                source='other',
                income_date__range=[period_start, period_end]
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            total_cash_inflows = cash_from_sales + cash_from_services + other_cash_inflows
            
            # Cash outflows
            cash_for_expenses = Expense.objects.filter(
                user=self.user,
                expense_date__range=[period_start, period_end]
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            cash_for_assets = Asset.objects.filter(
                user=self.user,
                purchase_date__range=[period_start, period_end]
            ).aggregate(total=Sum('purchase_value'))['total'] or Decimal('0.00')
            
            # Tax payments (simplified)
            from accounting.models import TurnoverTaxRecord
            cash_for_taxes = TurnoverTaxRecord.objects.filter(
                user=self.user,
                calculated_at__date__range=[period_start, period_end]
            ).aggregate(total=Sum('tax_due'))['total'] or Decimal('0.00')
            
            total_cash_outflows = cash_for_expenses + cash_for_assets + cash_for_taxes
            
            # Net cash flow
            net_cash_flow = total_cash_inflows - total_cash_outflows
            
            # Generate daily breakdown for trends
            daily_data = self._generate_daily_cash_flow(period_start, period_end)
            
            return {
                'period_start': period_start,
                'period_end': period_end,
                'cash_from_sales': cash_from_sales,
                'cash_from_services': cash_from_services,
                'other_cash_inflows': other_cash_inflows,
                'total_cash_inflows': total_cash_inflows,
                'cash_for_expenses': cash_for_expenses,
                'cash_for_assets': cash_for_assets,
                'cash_for_taxes': cash_for_taxes,
                'total_cash_outflows': total_cash_outflows,
                'net_cash_flow': net_cash_flow,
                'daily_inflows': daily_data['inflows'],
                'daily_outflows': daily_data['outflows']
            }
            
        except Exception as e:
            logger.error(f"Error generating cash flow report: {str(e)}")
            raise
    
    def generate_sales_trend_report(self, period_start: date, period_end: date, period_type: str = 'monthly') -> Dict:
        """
        Generate a Sales Trend report
        """
        try:
            from sales.models import Sale
            
            # Generate trend data based on period type
            if period_type == 'daily':
                trend_data = self._generate_daily_sales_trend(period_start, period_end)
            elif period_type == 'weekly':
                trend_data = self._generate_weekly_sales_trend(period_start, period_end)
            else:  # monthly
                trend_data = self._generate_monthly_sales_trend(period_start, period_end)
            
            # Calculate summary statistics
            total_sales = Sale.objects.filter(
                user=self.user,
                sale_date__range=[period_start, period_end]
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            
            period_count = len(trend_data)
            average_sales = total_sales / period_count if period_count > 0 else Decimal('0.00')
            
            # Find highest and lowest performing periods
            highest_sales_period = max(trend_data, key=lambda x: x['sales_amount']) if trend_data else {}
            lowest_sales_period = min(trend_data, key=lambda x: x['sales_amount']) if trend_data else {}
            
            # Calculate growth rate (comparing first and last periods)
            growth_rate = Decimal('0.00')
            trend_direction = 'stable'
            
            if len(trend_data) >= 2:
                first_period = trend_data[0]['sales_amount']
                last_period = trend_data[-1]['sales_amount']
                if first_period > 0:
                    growth_rate = ((last_period - first_period) / first_period) * 100
                    if growth_rate > 5:
                        trend_direction = 'up'
                    elif growth_rate < -5:
                        trend_direction = 'down'
            
            return {
                'period_start': period_start,
                'period_end': period_end,
                'period_type': period_type,
                'trend_data': trend_data,
                'total_sales': total_sales,
                'average_sales': average_sales,
                'highest_sales_period': highest_sales_period,
                'lowest_sales_period': lowest_sales_period,
                'growth_rate': growth_rate,
                'trend_direction': trend_direction
            }
            
        except Exception as e:
            logger.error(f"Error generating sales trend report: {str(e)}")
            raise
    
    def generate_expense_trend_report(self, period_start: date, period_end: date, period_type: str = 'monthly') -> Dict:
        """
        Generate an Expense Trend report
        """
        try:
            from accounting.models import Expense
            
            # Generate trend data
            if period_type == 'daily':
                trend_data = self._generate_daily_expense_trend(period_start, period_end)
            elif period_type == 'weekly':
                trend_data = self._generate_weekly_expense_trend(period_start, period_end)
            else:  # monthly
                trend_data = self._generate_monthly_expense_trend(period_start, period_end)
            
            # Generate category breakdown
            expense_categories = Expense.objects.filter(
                user=self.user,
                expense_date__range=[period_start, period_end]
            ).values('category__name').annotate(
                total_amount=Sum('amount'),
                transaction_count=Count('id')
            ).order_by('-total_amount')
            
            # Calculate summary statistics
            total_expenses = Expense.objects.filter(
                user=self.user,
                expense_date__range=[period_start, period_end]
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            period_count = len(trend_data)
            average_expenses = total_expenses / period_count if period_count > 0 else Decimal('0.00')
            
            # Find highest and lowest expense periods
            highest_expense_period = max(trend_data, key=lambda x: x['expense_amount']) if trend_data else {}
            lowest_expense_period = min(trend_data, key=lambda x: x['expense_amount']) if trend_data else {}
            
            return {
                'period_start': period_start,
                'period_end': period_end,
                'period_type': period_type,
                'trend_data': trend_data,
                'expense_categories': list(expense_categories),
                'total_expenses': total_expenses,
                'average_expenses': average_expenses,
                'highest_expense_period': highest_expense_period,
                'lowest_expense_period': lowest_expense_period
            }
            
        except Exception as e:
            logger.error(f"Error generating expense trend report: {str(e)}")
            raise
    
    def generate_tax_summary_report(self, period_start: date, period_end: date) -> Dict:
        """
        Generate a Tax Summary report with ZRA compliance
        """
        try:
            from accounting.models import IncomeRecord, TurnoverTaxRecord
            from sales.models import Sale
            from services.models import WorkRecord
            
            # Calculate total revenue from all sources
            sales_revenue = Sale.objects.filter(
                user=self.user,
                sale_date__range=[period_start, period_end]
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            
            service_revenue = WorkRecord.objects.filter(
                user=self.user,
                date_of_work__range=[period_start, period_end]
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            
            other_income = IncomeRecord.objects.filter(
                user=self.user,
                source='other',
                income_date__range=[period_start, period_end]
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            total_revenue = sales_revenue + service_revenue + other_income
            
            # ZRA Turnover Tax calculations
            tax_free_allowance = Decimal('1000.00')  # K1,000 monthly allowance
            turnover_tax_rate = Decimal('5.00')  # 5% rate
            annual_turnover_limit = Decimal('5000000.00')  # K5M annual limit
            
            # Calculate monthly breakdown
            monthly_breakdown = []
            current_date = period_start
            
            while current_date <= period_end:
                month_start = current_date.replace(day=1)
                next_month = (month_start + timedelta(days=32)).replace(day=1)
                month_end = min(next_month - timedelta(days=1), period_end)
                
                # Monthly revenue
                monthly_sales = Sale.objects.filter(
                    user=self.user,
                    sale_date__range=[month_start, month_end]
                ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
                
                monthly_services = WorkRecord.objects.filter(
                    user=self.user,
                    date_of_work__range=[month_start, month_end]
                ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
                
                monthly_revenue = monthly_sales + monthly_services
                
                # Tax calculation
                taxable_amount = max(monthly_revenue - tax_free_allowance, Decimal('0.00'))
                monthly_tax = (taxable_amount * turnover_tax_rate / 100).quantize(Decimal('0.01'))
                
                monthly_breakdown.append({
                    'month': month_start.strftime('%Y-%m'),
                    'month_name': month_start.strftime('%B %Y'),
                    'total_revenue': monthly_revenue,
                    'tax_free_allowance': tax_free_allowance,
                    'taxable_income': taxable_amount,
                    'tax_due': monthly_tax
                })
                
                current_date = next_month
            
            # Calculate total taxable income and tax due
            total_taxable_income = sum(month['taxable_income'] for month in monthly_breakdown)
            total_tax_due = sum(month['tax_due'] for month in monthly_breakdown)
            
            # Check annual turnover eligibility
            current_year_start = date(period_start.year, 1, 1)
            current_year_end = date(period_start.year, 12, 31)
            
            annual_turnover = Sale.objects.filter(
                user=self.user,
                sale_date__range=[current_year_start, current_year_end]
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            
            annual_service_revenue = WorkRecord.objects.filter(
                user=self.user,
                date_of_work__range=[current_year_start, current_year_end]
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            
            current_annual_turnover = annual_turnover + annual_service_revenue
            is_eligible_for_turnover_tax = current_annual_turnover <= annual_turnover_limit
            
            return {
                'period_start': period_start,
                'period_end': period_end,
                'total_revenue': total_revenue,
                'tax_free_allowance': tax_free_allowance,
                'taxable_income': total_taxable_income,
                'turnover_tax_rate': turnover_tax_rate,
                'turnover_tax_due': total_tax_due,
                'monthly_breakdown': monthly_breakdown,
                'annual_turnover_limit': annual_turnover_limit,
                'current_annual_turnover': current_annual_turnover,
                'is_eligible_for_turnover_tax': is_eligible_for_turnover_tax
            }
            
        except Exception as e:
            logger.error(f"Error generating tax summary report: {str(e)}")
            raise
    
    def generate_business_overview_report(self, period_start: date, period_end: date) -> Dict:
        """
        Generate a comprehensive business overview report
        """
        try:
            # Get all component reports
            profit_loss = self.generate_profit_loss_report(period_start, period_end)
            tax_summary = self.generate_tax_summary_report(period_start, period_end)
            
            # Additional metrics
            from sales.models import Sale, SaleItem
            from services.models import WorkRecord
            from inventory.models import Product
            
            # Operational metrics
            total_sales_transactions = Sale.objects.filter(
                user=self.user,
                sale_date__range=[period_start, period_end]
            ).count()
            
            total_service_hours = WorkRecord.objects.filter(
                user=self.user,
                date_of_work__range=[period_start, period_end]
            ).aggregate(total=Sum('hours_worked'))['total'] or Decimal('0.00')
            
            total_products_sold = SaleItem.objects.filter(
                sale__user=self.user,
                sale__sale_date__range=[period_start, period_end]
            ).aggregate(total=Sum('quantity'))['total'] or 0
            
            # Growth calculations (compare to previous period)
            prev_period_start = period_start - timedelta(days=(period_end - period_start).days + 1)
            prev_period_end = period_start - timedelta(days=1)
            
            prev_revenue = Sale.objects.filter(
                user=self.user,
                sale_date__range=[prev_period_start, prev_period_end]
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            
            revenue_growth = Decimal('0.00')
            if prev_revenue > 0:
                revenue_growth = ((profit_loss['total_income'] - prev_revenue) / prev_revenue * 100)
            
            # Top performers
            top_selling_products = SaleItem.objects.filter(
                sale__user=self.user,
                sale__sale_date__range=[period_start, period_end]
            ).values(
                'product__name'
            ).annotate(
                total_quantity=Sum('quantity'),
                total_revenue=Sum(F('quantity') * F('unit_price'))
            ).order_by('-total_revenue')[:5]
            
            top_services = WorkRecord.objects.filter(
                user=self.user,
                date_of_work__range=[period_start, period_end]
            ).values(
                'service__name'
            ).annotate(
                total_revenue=Sum('total_amount'),
                total_hours=Sum('hours_worked')
            ).order_by('-total_revenue')[:5]
            
            return {
                'period_start': period_start,
                'period_end': period_end,
                'total_revenue': profit_loss['total_income'],
                'total_expenses': profit_loss['total_expenses'],
                'net_profit': profit_loss['net_profit'],
                'profit_margin': profit_loss['net_margin_percentage'],
                'total_sales_transactions': total_sales_transactions,
                'total_service_hours': total_service_hours,
                'total_products_sold': total_products_sold,
                'revenue_growth': revenue_growth,
                'expense_growth': Decimal('0.00'),  # Can be calculated similarly
                'customer_growth': Decimal('0.00'),  # To be implemented with customer tracking
                'total_tax_due': tax_summary['turnover_tax_due'],
                'effective_tax_rate': tax_summary['turnover_tax_rate'],
                'top_selling_products': list(top_selling_products),
                'top_services': list(top_services),
                'top_expense_categories': []  # From expense trend report
            }
            
        except Exception as e:
            logger.error(f"Error generating business overview report: {str(e)}")
            raise
    
    # Helper methods for trend generation
    def _generate_daily_sales_trend(self, period_start: date, period_end: date) -> List[Dict]:
        """Generate daily sales trend data"""
        from sales.models import Sale
        
        trend_data = []
        current_date = period_start
        
        while current_date <= period_end:
            daily_sales = Sale.objects.filter(
                user=self.user,
                sale_date=current_date
            ).aggregate(
                total_amount=Sum('total_amount'),
                transaction_count=Count('id')
            )
            
            trend_data.append({
                'date': current_date.isoformat(),
                'period_label': current_date.strftime('%Y-%m-%d'),
                'sales_amount': daily_sales['total_amount'] or Decimal('0.00'),
                'transaction_count': daily_sales['transaction_count'] or 0
            })
            
            current_date += timedelta(days=1)
        
        return trend_data
    
    def _generate_monthly_sales_trend(self, period_start: date, period_end: date) -> List[Dict]:
        """Generate monthly sales trend data"""
        from sales.models import Sale
        
        trend_data = []
        current_date = period_start.replace(day=1)
        
        while current_date <= period_end:
            next_month = (current_date + timedelta(days=32)).replace(day=1)
            month_end = min(next_month - timedelta(days=1), period_end)
            
            monthly_sales = Sale.objects.filter(
                user=self.user,
                sale_date__range=[current_date, month_end]
            ).aggregate(
                total_amount=Sum('total_amount'),
                transaction_count=Count('id')
            )
            
            trend_data.append({
                'date': current_date.isoformat(),
                'period_label': current_date.strftime('%B %Y'),
                'sales_amount': monthly_sales['total_amount'] or Decimal('0.00'),
                'transaction_count': monthly_sales['transaction_count'] or 0
            })
            
            current_date = next_month
        
        return trend_data
    
    def _generate_weekly_sales_trend(self, period_start: date, period_end: date) -> List[Dict]:
        """Generate weekly sales trend data"""
        from sales.models import Sale
        
        trend_data = []
        # Start from the beginning of the week
        current_date = period_start - timedelta(days=period_start.weekday())
        
        while current_date <= period_end:
            week_end = min(current_date + timedelta(days=6), period_end)
            
            weekly_sales = Sale.objects.filter(
                user=self.user,
                sale_date__range=[max(current_date, period_start), week_end]
            ).aggregate(
                total_amount=Sum('total_amount'),
                transaction_count=Count('id')
            )
            
            trend_data.append({
                'date': current_date.isoformat(),
                'period_label': f"Week of {current_date.strftime('%Y-%m-%d')}",
                'sales_amount': weekly_sales['total_amount'] or Decimal('0.00'),
                'transaction_count': weekly_sales['transaction_count'] or 0
            })
            
            current_date += timedelta(days=7)
        
        return trend_data
    
    def _generate_daily_expense_trend(self, period_start: date, period_end: date) -> List[Dict]:
        """Generate daily expense trend data"""
        from accounting.models import Expense
        
        trend_data = []
        current_date = period_start
        
        while current_date <= period_end:
            daily_expenses = Expense.objects.filter(
                user=self.user,
                expense_date=current_date
            ).aggregate(
                total_amount=Sum('amount'),
                transaction_count=Count('id')
            )
            
            trend_data.append({
                'date': current_date.isoformat(),
                'period_label': current_date.strftime('%Y-%m-%d'),
                'expense_amount': daily_expenses['total_amount'] or Decimal('0.00'),
                'transaction_count': daily_expenses['transaction_count'] or 0
            })
            
            current_date += timedelta(days=1)
        
        return trend_data
    
    def _generate_monthly_expense_trend(self, period_start: date, period_end: date) -> List[Dict]:
        """Generate monthly expense trend data"""
        from accounting.models import Expense
        
        trend_data = []
        current_date = period_start.replace(day=1)
        
        while current_date <= period_end:
            next_month = (current_date + timedelta(days=32)).replace(day=1)
            month_end = min(next_month - timedelta(days=1), period_end)
            
            monthly_expenses = Expense.objects.filter(
                user=self.user,
                expense_date__range=[current_date, month_end]
            ).aggregate(
                total_amount=Sum('amount'),
                transaction_count=Count('id')
            )
            
            trend_data.append({
                'date': current_date.isoformat(),
                'period_label': current_date.strftime('%B %Y'),
                'expense_amount': monthly_expenses['total_amount'] or Decimal('0.00'),
                'transaction_count': monthly_expenses['transaction_count'] or 0
            })
            
            current_date = next_month
        
        return trend_data
    
    def _generate_weekly_expense_trend(self, period_start: date, period_end: date) -> List[Dict]:
        """Generate weekly expense trend data"""
        from accounting.models import Expense
        
        trend_data = []
        current_date = period_start - timedelta(days=period_start.weekday())
        
        while current_date <= period_end:
            week_end = min(current_date + timedelta(days=6), period_end)
            
            weekly_expenses = Expense.objects.filter(
                user=self.user,
                expense_date__range=[max(current_date, period_start), week_end]
            ).aggregate(
                total_amount=Sum('amount'),
                transaction_count=Count('id')
            )
            
            trend_data.append({
                'date': current_date.isoformat(),
                'period_label': f"Week of {current_date.strftime('%Y-%m-%d')}",
                'expense_amount': weekly_expenses['total_amount'] or Decimal('0.00'),
                'transaction_count': weekly_expenses['transaction_count'] or 0
            })
            
            current_date += timedelta(days=7)
        
        return trend_data
    
    def _generate_daily_cash_flow(self, period_start: date, period_end: date) -> Dict:
        """Generate daily cash flow data"""
        from sales.models import Sale
        from services.models import WorkRecord
        from accounting.models import Expense
        
        inflows = []
        outflows = []
        current_date = period_start
        
        while current_date <= period_end:
            # Daily inflows
            daily_sales = Sale.objects.filter(
                user=self.user,
                sale_date=current_date
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            
            daily_services = WorkRecord.objects.filter(
                user=self.user,
                date_of_work=current_date
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            
            inflows.append({
                'date': current_date.isoformat(),
                'sales': daily_sales,
                'services': daily_services,
                'total': daily_sales + daily_services
            })
            
            # Daily outflows
            daily_expenses = Expense.objects.filter(
                user=self.user,
                expense_date=current_date
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            outflows.append({
                'date': current_date.isoformat(),
                'expenses': daily_expenses,
                'total': daily_expenses
            })
            
            current_date += timedelta(days=1)
        
        return {
            'inflows': inflows,
            'outflows': outflows
        }


class ReportCache:
    """
    Utility class for managing report caching
    """
    
    @staticmethod
    def get_cached_report(user, report_type: str, period_start: date, period_end: date) -> Optional[ReportSnapshot]:
        """
        Get a cached report if available and still valid
        """
        try:
            return ReportSnapshot.objects.get(
                user=user,
                report_type=report_type,
                period_start=period_start,
                period_end=period_end,
                is_cached=True
            )
        except ReportSnapshot.DoesNotExist:
            return None
    
    @staticmethod
    def cache_report(user, report_type: str, period_start: date, period_end: date, report_data: Dict) -> ReportSnapshot:
        """
        Cache a report for future use
        """
        snapshot, created = ReportSnapshot.objects.update_or_create(
            user=user,
            report_type=report_type,
            period_start=period_start,
            period_end=period_end,
            defaults={
                'total_income': report_data.get('total_income', Decimal('0.00')),
                'total_expenses': report_data.get('total_expenses', Decimal('0.00')),
                'net_profit': report_data.get('net_profit', Decimal('0.00')),
                'total_sales_count': report_data.get('number_of_transactions', 0),
                'total_sales_amount': report_data.get('sales_revenue', Decimal('0.00')),
                'average_sale_value': report_data.get('average_transaction_value', Decimal('0.00')),
                'total_service_hours': report_data.get('total_service_hours', Decimal('0.00')),
                'total_service_revenue': report_data.get('service_revenue', Decimal('0.00')),
                'taxable_income': report_data.get('taxable_income', Decimal('0.00')),
                'turnover_tax_due': report_data.get('turnover_tax_due', Decimal('0.00')),
                'additional_data': json.loads(json.dumps(report_data, cls=DecimalEncoder)),
                'is_cached': True
            }
        )
        return snapshot
