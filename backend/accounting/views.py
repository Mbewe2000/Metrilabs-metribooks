from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Sum, Q, Count
from django.utils import timezone
from datetime import date, timedelta, datetime
from decimal import Decimal
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
import logging

from .models import (
    Expense, ExpenseCategory, Asset, AssetCategory,
    IncomeRecord, TurnoverTaxRecord, FinancialSummary
)
from .serializers import (
    ExpenseSerializer, ExpenseCreateSerializer, ExpenseCategorySerializer,
    AssetSerializer, AssetCreateSerializer, AssetCategorySerializer,
    IncomeRecordSerializer, TurnoverTaxRecordSerializer, FinancialSummarySerializer,
    ProfitLossReportSerializer, CashFlowReportSerializer, TurnoverTaxReportSerializer,
    DashboardSerializer, ExpenseAnalysisSerializer
)

logger = logging.getLogger('accounting')


# ===============================
# Expense Management Views
# ===============================

class ExpenseCategoryListView(generics.ListAPIView):
    """List all expense categories"""
    serializer_class = ExpenseCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return ExpenseCategory.objects.filter(is_active=True)


class ExpenseListView(generics.ListAPIView):
    """List expenses with filtering options"""
    serializer_class = ExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Expense.objects.filter(user=self.request.user).select_related('category')
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(expense_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(expense_date__lte=end_date)
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__name=category)
        
        # Filter by payment status
        payment_status = self.request.query_params.get('payment_status')
        if payment_status:
            queryset = queryset.filter(payment_status=payment_status)
        
        # Filter by expense type
        expense_type = self.request.query_params.get('expense_type')
        if expense_type:
            queryset = queryset.filter(expense_type=expense_type)
        
        return queryset.order_by('-expense_date')


class ExpenseCreateView(generics.CreateAPIView):
    """Create a new expense"""
    serializer_class = ExpenseCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @method_decorator(ratelimit(key='user', rate='100/h', method='POST'))
    def post(self, request, *args, **kwargs):
        try:
            response = super().create(request, *args, **kwargs)
            
            logger.info(f"Expense created by user: {request.user.email}")
            return Response({
                'success': True,
                'message': 'Expense created successfully',
                'data': response.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error creating expense for user {request.user.email}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error creating expense',
                'errors': [str(e)]
            }, status=status.HTTP_400_BAD_REQUEST)


class ExpenseDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete an expense"""
    serializer_class = ExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Expense.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ExpenseCreateSerializer
        return ExpenseSerializer


# ===============================
# Asset Management Views
# ===============================

class AssetCategoryListView(generics.ListAPIView):
    """List all asset categories"""
    serializer_class = AssetCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return AssetCategory.objects.filter(is_active=True)


class AssetListView(generics.ListAPIView):
    """List assets with filtering options"""
    serializer_class = AssetSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Asset.objects.filter(user=self.request.user).select_related('category')
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__name=category)
        
        # Filter by status
        asset_status = self.request.query_params.get('status')
        if asset_status:
            queryset = queryset.filter(status=asset_status)
        
        # Filter by purchase date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(purchase_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(purchase_date__lte=end_date)
        
        return queryset.order_by('-purchase_date')


class AssetCreateView(generics.CreateAPIView):
    """Create a new asset"""
    serializer_class = AssetCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @method_decorator(ratelimit(key='user', rate='50/h', method='POST'))
    def post(self, request, *args, **kwargs):
        try:
            response = super().create(request, *args, **kwargs)
            
            logger.info(f"Asset created by user: {request.user.email}")
            return Response({
                'success': True,
                'message': 'Asset created successfully',
                'data': response.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error creating asset for user {request.user.email}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error creating asset',
                'errors': [str(e)]
            }, status=status.HTTP_400_BAD_REQUEST)


class AssetDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete an asset"""
    serializer_class = AssetSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Asset.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return AssetCreateSerializer
        return AssetSerializer


# ===============================
# Income Tracking Views
# ===============================

class IncomeRecordListView(generics.ListAPIView):
    """List income records with filtering options"""
    serializer_class = IncomeRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = IncomeRecord.objects.filter(user=self.request.user)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(income_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(income_date__lte=end_date)
        
        # Filter by source
        source = self.request.query_params.get('source')
        if source:
            queryset = queryset.filter(source=source)
        
        return queryset.order_by('-income_date')


# ===============================
# Tax Management Views
# ===============================

class TurnoverTaxRecordListView(generics.ListAPIView):
    """List turnover tax records"""
    serializer_class = TurnoverTaxRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = TurnoverTaxRecord.objects.filter(user=self.request.user)
        
        # Filter by year
        year = self.request.query_params.get('year')
        if year:
            queryset = queryset.filter(year=year)
        
        return queryset.order_by('-year', '-month')


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@ratelimit(key='user', rate='10/h', method='POST')
def calculate_turnover_tax(request):
    """Calculate turnover tax for a specific month"""
    try:
        year = int(request.data.get('year', timezone.now().year))
        month = int(request.data.get('month', timezone.now().month))
        
        # Get or create tax record
        tax_record, created = TurnoverTaxRecord.objects.get_or_create(
            user=request.user,
            year=year,
            month=month,
            defaults={
                'total_revenue': Decimal('0.00')
            }
        )
        
        # Calculate revenue for the month
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)
        
        monthly_income = IncomeRecord.objects.filter(
            user=request.user,
            income_date__gte=start_date,
            income_date__lt=end_date
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        tax_record.total_revenue = monthly_income
        tax_record.calculate_tax()
        
        serializer = TurnoverTaxRecordSerializer(tax_record)
        
        return Response({
            'success': True,
            'message': 'Turnover tax calculated successfully',
            'data': serializer.data
        })
        
    except Exception as e:
        logger.error(f"Error calculating turnover tax for user {request.user.email}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Error calculating turnover tax',
            'errors': [str(e)]
        }, status=status.HTTP_400_BAD_REQUEST)


# ===============================
# Financial Reports Views
# ===============================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def profit_loss_report(request):
    """Generate Profit & Loss report"""
    try:
        # Get date parameters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            # Default to current month
            today = date.today()
            start_date = date(today.year, today.month, 1)
            if today.month == 12:
                end_date = date(today.year + 1, 1, 1)
            else:
                end_date = date(today.year, today.month + 1, 1)
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Calculate total income
        income_data = IncomeRecord.objects.filter(
            user=request.user,
            income_date__gte=start_date,
            income_date__lte=end_date
        )
        
        total_income = income_data.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Income breakdown by source
        income_breakdown = {}
        for source_code, source_name in IncomeRecord.INCOME_SOURCE_CHOICES:
            amount = income_data.filter(source=source_code).aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0.00')
            income_breakdown[source_name] = float(amount)
        
        # Calculate total expenses
        expense_data = Expense.objects.filter(
            user=request.user,
            expense_date__gte=start_date,
            expense_date__lte=end_date,
            payment_status='paid'
        )
        
        total_expenses = expense_data.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Expense breakdown by category
        expense_breakdown = {}
        for category in ExpenseCategory.objects.filter(is_active=True):
            amount = expense_data.filter(category=category).aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0.00')
            expense_breakdown[str(category)] = float(amount)
        
        # Calculate metrics
        net_profit = total_income - total_expenses
        profit_margin = (net_profit / total_income * 100) if total_income > 0 else Decimal('0.00')
        
        report_data = {
            'period_start': start_date,
            'period_end': end_date,
            'total_income': total_income,
            'income_breakdown': income_breakdown,
            'total_expenses': total_expenses,
            'expense_breakdown': expense_breakdown,
            'net_profit': net_profit,
            'profit_margin': profit_margin
        }
        
        serializer = ProfitLossReportSerializer(report_data)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
        
    except Exception as e:
        logger.error(f"Error generating P&L report for user {request.user.email}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Error generating profit & loss report',
            'errors': [str(e)]
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def turnover_tax_report(request):
    """Generate annual turnover tax report"""
    try:
        year = int(request.query_params.get('year', timezone.now().year))
        
        # Get all tax records for the year
        tax_records = TurnoverTaxRecord.objects.filter(
            user=request.user,
            year=year
        ).order_by('month')
        
        # Calculate totals
        annual_revenue = tax_records.aggregate(
            total=Sum('total_revenue')
        )['total'] or Decimal('0.00')
        
        annual_tax_due = tax_records.aggregate(
            total=Sum('tax_due')
        )['total'] or Decimal('0.00')
        
        # Monthly breakdown
        monthly_breakdown = []
        for record in tax_records:
            monthly_breakdown.append({
                'month': record.month,
                'month_name': date(year, record.month, 1).strftime('%B'),
                'revenue': float(record.total_revenue),
                'tax_due': float(record.tax_due),
                'payment_status': record.payment_status
            })
        
        # Check eligibility
        is_eligible = annual_revenue <= Decimal('5000000.00')
        exceeds_threshold = annual_revenue > Decimal('5000000.00')
        
        report_data = {
            'year': year,
            'annual_revenue': annual_revenue,
            'annual_tax_due': annual_tax_due,
            'monthly_breakdown': monthly_breakdown,
            'is_eligible_for_turnover_tax': is_eligible,
            'exceeds_annual_threshold': exceeds_threshold
        }
        
        serializer = TurnoverTaxReportSerializer(report_data)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
        
    except Exception as e:
        logger.error(f"Error generating tax report for user {request.user.email}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Error generating turnover tax report',
            'errors': [str(e)]
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def expense_analysis_report(request):
    """Generate expense analysis report"""
    try:
        # Get date parameters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            # Default to current year
            today = date.today()
            start_date = date(today.year, 1, 1)
            end_date = date(today.year, 12, 31)
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Get expense data
        expenses = Expense.objects.filter(
            user=request.user,
            expense_date__gte=start_date,
            expense_date__lte=end_date
        )
        
        total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Category breakdown
        category_breakdown = {}
        for category in ExpenseCategory.objects.filter(is_active=True):
            amount = expenses.filter(category=category).aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0.00')
            category_breakdown[str(category)] = float(amount)
        
        # Top expenses
        top_expenses = []
        for expense in expenses.order_by('-amount')[:10]:
            top_expenses.append({
                'name': expense.name,
                'amount': float(expense.amount),
                'date': expense.expense_date.isoformat(),
                'category': str(expense.category)
            })
        
        # Recurring vs one-time
        recurring_total = expenses.filter(expense_type='recurring').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        one_time_total = expenses.filter(expense_type='one_time').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        recurring_vs_one_time = {
            'recurring': float(recurring_total),
            'one_time': float(one_time_total)
        }
        
        # Payment status breakdown
        payment_breakdown = {}
        for status_code, status_name in Expense.PAYMENT_STATUS_CHOICES:
            count = expenses.filter(payment_status=status_code).count()
            amount = expenses.filter(payment_status=status_code).aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0.00')
            payment_breakdown[status_name] = {
                'count': count,
                'amount': float(amount)
            }
        
        # Monthly trend (if more than one month in range)
        monthly_trend = []
        current_date = start_date.replace(day=1)
        while current_date <= end_date:
            month_end = date(current_date.year, current_date.month, 1)
            if current_date.month == 12:
                month_end = date(current_date.year + 1, 1, 1)
            else:
                month_end = date(current_date.year, current_date.month + 1, 1)
            
            month_total = expenses.filter(
                expense_date__gte=current_date,
                expense_date__lt=month_end
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            monthly_trend.append({
                'month': current_date.strftime('%Y-%m'),
                'amount': float(month_total)
            })
            
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        report_data = {
            'period_start': start_date,
            'period_end': end_date,
            'total_expenses': total_expenses,
            'category_breakdown': category_breakdown,
            'monthly_trend': monthly_trend,
            'top_expenses': top_expenses,
            'recurring_vs_one_time': recurring_vs_one_time,
            'payment_status_breakdown': payment_breakdown
        }
        
        serializer = ExpenseAnalysisSerializer(report_data)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
        
    except Exception as e:
        logger.error(f"Error generating expense analysis for user {request.user.email}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Error generating expense analysis report',
            'errors': [str(e)]
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def financial_dashboard(request):
    """Get financial dashboard data"""
    try:
        today = date.today()
        current_month_start = date(today.year, today.month, 1)
        year_start = date(today.year, 1, 1)
        
        # Current month metrics
        current_month_income = IncomeRecord.objects.filter(
            user=request.user,
            income_date__gte=current_month_start,
            income_date__lte=today
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        current_month_expenses = Expense.objects.filter(
            user=request.user,
            expense_date__gte=current_month_start,
            expense_date__lte=today,
            payment_status='paid'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        current_month_profit = current_month_income - current_month_expenses
        
        # Get current month tax
        try:
            current_tax = TurnoverTaxRecord.objects.get(
                user=request.user,
                year=today.year,
                month=today.month
            )
            current_month_tax_due = current_tax.tax_due
        except TurnoverTaxRecord.DoesNotExist:
            current_month_tax_due = Decimal('0.00')
        
        # Year-to-date metrics
        ytd_income = IncomeRecord.objects.filter(
            user=request.user,
            income_date__gte=year_start,
            income_date__lte=today
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        ytd_expenses = Expense.objects.filter(
            user=request.user,
            expense_date__gte=year_start,
            expense_date__lte=today,
            payment_status='paid'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        ytd_profit = ytd_income - ytd_expenses
        
        ytd_tax_due = TurnoverTaxRecord.objects.filter(
            user=request.user,
            year=today.year
        ).aggregate(total=Sum('tax_due'))['total'] or Decimal('0.00')
        
        # Asset metrics
        total_assets = Asset.objects.filter(
            user=request.user,
            status='active'
        ).aggregate(
            total=Sum('current_value')
        )['total'] or Asset.objects.filter(
            user=request.user,
            status='active'
        ).aggregate(
            total=Sum('purchase_value')
        )['total'] or Decimal('0.00')
        
        # Outstanding items
        unpaid_expenses = Expense.objects.filter(
            user=request.user,
            payment_status='unpaid'
        ).count()
        
        overdue_expenses = Expense.objects.filter(
            user=request.user,
            payment_status='overdue'
        ).count()
        
        unpaid_taxes = TurnoverTaxRecord.objects.filter(
            user=request.user,
            payment_status='pending'
        ).count()
        
        # Dashboard data
        dashboard_data = {
            'current_month_income': current_month_income,
            'current_month_expenses': current_month_expenses,
            'current_month_profit': current_month_profit,
            'current_month_tax_due': current_month_tax_due,
            'ytd_income': ytd_income,
            'ytd_expenses': ytd_expenses,
            'ytd_profit': ytd_profit,
            'ytd_tax_due': ytd_tax_due,
            'total_assets': total_assets,
            'unpaid_expenses': unpaid_expenses,
            'overdue_expenses': overdue_expenses,
            'unpaid_taxes': unpaid_taxes,
            'monthly_profit_trend': [],  # TODO: Implement
            'expense_breakdown': {},     # TODO: Implement
            'income_sources': {},        # TODO: Implement
            'recent_income': [],         # TODO: Implement
            'recent_expenses': [],       # TODO: Implement
            'alerts': []                 # TODO: Implement
        }
        
        serializer = DashboardSerializer(dashboard_data)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
        
    except Exception as e:
        logger.error(f"Error generating dashboard for user {request.user.email}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Error loading financial dashboard',
            'errors': [str(e)]
        }, status=status.HTTP_400_BAD_REQUEST)
