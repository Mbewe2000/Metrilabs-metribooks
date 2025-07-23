from rest_framework import status, generics, permissions, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum, Count, Avg, F
from django.utils import timezone
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from decimal import Decimal
from datetime import date, datetime, timedelta
import logging

from .models import ReportSnapshot, ReportTemplate, BusinessMetric
from .serializers import (
    ReportSnapshotSerializer,
    ReportTemplateSerializer,
    BusinessMetricSerializer,
    ProfitLossReportSerializer,
    CashFlowReportSerializer,
    SalesTrendReportSerializer,
    ExpenseTrendReportSerializer,
    TaxSummaryReportSerializer,
    BusinessOverviewReportSerializer,
    ReportGenerationRequestSerializer
)
from .utils import ReportGenerator, ReportCache

# Get logger
logger = logging.getLogger('reports')


# ===============================
# Report Generation Views
# ===============================

class ReportGenerationView(APIView):
    """
    Generate reports on demand with caching support
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @method_decorator(ratelimit(key='user', rate='20/m', method='POST'))
    def post(self, request):
        """Generate a specific report"""
        serializer = ReportGenerationRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        report_type = serializer.validated_data['report_type']
        period_start = serializer.validated_data['period_start']
        period_end = serializer.validated_data['period_end']
        force_regenerate = serializer.validated_data.get('force_regenerate', False)
        
        try:
            # Check for cached report if not forcing regeneration
            if not force_regenerate:
                cached_report = ReportCache.get_cached_report(
                    request.user, report_type, period_start, period_end
                )
                if cached_report:
                    return Response({
                        'report_type': report_type,
                        'cached': True,
                        'data': cached_report.additional_data,
                        'generated_at': cached_report.generated_at
                    })
            
            # Generate new report
            generator = ReportGenerator(request.user)
            
            if report_type == 'profit_loss':
                report_data = generator.generate_profit_loss_report(period_start, period_end)
                serializer_class = ProfitLossReportSerializer
            elif report_type == 'cash_flow':
                report_data = generator.generate_cash_flow_report(period_start, period_end)
                serializer_class = CashFlowReportSerializer
            elif report_type == 'sales_trend':
                period_type = request.data.get('period_type', 'monthly')
                report_data = generator.generate_sales_trend_report(period_start, period_end, period_type)
                serializer_class = SalesTrendReportSerializer
            elif report_type == 'expense_trend':
                period_type = request.data.get('period_type', 'monthly')
                report_data = generator.generate_expense_trend_report(period_start, period_end, period_type)
                serializer_class = ExpenseTrendReportSerializer
            elif report_type == 'tax_summary':
                report_data = generator.generate_tax_summary_report(period_start, period_end)
                serializer_class = TaxSummaryReportSerializer
            elif report_type == 'business_overview':
                report_data = generator.generate_business_overview_report(period_start, period_end)
                serializer_class = BusinessOverviewReportSerializer
            else:
                return Response(
                    {'error': f'Unsupported report type: {report_type}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Cache the report
            ReportCache.cache_report(request.user, report_type, period_start, period_end, report_data)
            
            # Serialize and return the report
            serialized_data = serializer_class(report_data)
            
            return Response({
                'report_type': report_type,
                'cached': False,
                'data': serialized_data.data,
                'generated_at': timezone.now()
            })
            
        except Exception as e:
            logger.error(f"Error generating report {report_type}: {str(e)}")
            return Response(
                {'error': 'An error occurred while generating the report'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ===============================
# Quick Report Views
# ===============================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
@ratelimit(key='user', rate='30/m', method='GET')
def profit_loss_summary(request):
    """
    Quick Profit & Loss summary for current month
    """
    try:
        # Default to current month
        today = date.today()
        period_start = today.replace(day=1)
        period_end = today
        
        # Allow custom period via query parameters
        if 'start_date' in request.GET:
            period_start = datetime.strptime(request.GET['start_date'], '%Y-%m-%d').date()
        if 'end_date' in request.GET:
            period_end = datetime.strptime(request.GET['end_date'], '%Y-%m-%d').date()
        
        generator = ReportGenerator(request.user)
        report_data = generator.generate_profit_loss_report(period_start, period_end)
        
        serializer = ProfitLossReportSerializer(report_data)
        return Response(serializer.data)
        
    except Exception as e:
        logger.error(f"Error generating profit/loss summary: {str(e)}")
        return Response(
            {'error': 'Error generating profit/loss summary'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
@ratelimit(key='user', rate='30/m', method='GET')
def cash_flow_summary(request):
    """
    Quick Cash Flow summary for current month
    """
    try:
        today = date.today()
        period_start = today.replace(day=1)
        period_end = today
        
        if 'start_date' in request.GET:
            period_start = datetime.strptime(request.GET['start_date'], '%Y-%m-%d').date()
        if 'end_date' in request.GET:
            period_end = datetime.strptime(request.GET['end_date'], '%Y-%m-%d').date()
        
        generator = ReportGenerator(request.user)
        report_data = generator.generate_cash_flow_report(period_start, period_end)
        
        serializer = CashFlowReportSerializer(report_data)
        return Response(serializer.data)
        
    except Exception as e:
        logger.error(f"Error generating cash flow summary: {str(e)}")
        return Response(
            {'error': 'Error generating cash flow summary'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
@ratelimit(key='user', rate='20/m', method='GET')
def sales_trends(request):
    """
    Sales trend analysis with customizable period
    """
    try:
        # Default to last 6 months
        today = date.today()
        period_end = today
        period_start = today - timedelta(days=180)
        
        if 'start_date' in request.GET:
            period_start = datetime.strptime(request.GET['start_date'], '%Y-%m-%d').date()
        if 'end_date' in request.GET:
            period_end = datetime.strptime(request.GET['end_date'], '%Y-%m-%d').date()
        
        period_type = request.GET.get('period_type', 'monthly')
        
        generator = ReportGenerator(request.user)
        report_data = generator.generate_sales_trend_report(period_start, period_end, period_type)
        
        serializer = SalesTrendReportSerializer(report_data)
        return Response(serializer.data)
        
    except Exception as e:
        logger.error(f"Error generating sales trends: {str(e)}")
        return Response(
            {'error': 'Error generating sales trends'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
@ratelimit(key='user', rate='20/m', method='GET')
def expense_trends(request):
    """
    Expense trend analysis with customizable period
    """
    try:
        today = date.today()
        period_end = today
        period_start = today - timedelta(days=180)
        
        if 'start_date' in request.GET:
            period_start = datetime.strptime(request.GET['start_date'], '%Y-%m-%d').date()
        if 'end_date' in request.GET:
            period_end = datetime.strptime(request.GET['end_date'], '%Y-%m-%d').date()
        
        period_type = request.GET.get('period_type', 'monthly')
        
        generator = ReportGenerator(request.user)
        report_data = generator.generate_expense_trend_report(period_start, period_end, period_type)
        
        serializer = ExpenseTrendReportSerializer(report_data)
        return Response(serializer.data)
        
    except Exception as e:
        logger.error(f"Error generating expense trends: {str(e)}")
        return Response(
            {'error': 'Error generating expense trends'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
@ratelimit(key='user', rate='30/m', method='GET')
def tax_summary(request):
    """
    Tax summary with ZRA compliance information
    """
    try:
        today = date.today()
        period_start = today.replace(day=1)
        period_end = today
        
        if 'start_date' in request.GET:
            period_start = datetime.strptime(request.GET['start_date'], '%Y-%m-%d').date()
        if 'end_date' in request.GET:
            period_end = datetime.strptime(request.GET['end_date'], '%Y-%m-%d').date()
        
        generator = ReportGenerator(request.user)
        report_data = generator.generate_tax_summary_report(period_start, period_end)
        
        serializer = TaxSummaryReportSerializer(report_data)
        return Response(serializer.data)
        
    except Exception as e:
        logger.error(f"Error generating tax summary: {str(e)}")
        return Response(
            {'error': 'Error generating tax summary'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
@ratelimit(key='user', rate='20/m', method='GET')
def business_overview(request):
    """
    Comprehensive business overview dashboard
    """
    try:
        today = date.today()
        period_start = today.replace(day=1)
        period_end = today
        
        if 'start_date' in request.GET:
            period_start = datetime.strptime(request.GET['start_date'], '%Y-%m-%d').date()
        if 'end_date' in request.GET:
            period_end = datetime.strptime(request.GET['end_date'], '%Y-%m-%d').date()
        
        generator = ReportGenerator(request.user)
        report_data = generator.generate_business_overview_report(period_start, period_end)
        
        serializer = BusinessOverviewReportSerializer(report_data)
        return Response(serializer.data)
        
    except Exception as e:
        logger.error(f"Error generating business overview: {str(e)}")
        return Response(
            {'error': 'Error generating business overview'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ===============================
# Report Management Views
# ===============================

class ReportSnapshotViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for report snapshots
    """
    serializer_class = ReportSnapshotSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter snapshots by user"""
        return ReportSnapshot.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Automatically set user when creating"""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent report snapshots"""
        recent_snapshots = self.get_queryset().order_by('-generated_at')[:10]
        serializer = self.get_serializer(recent_snapshots, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def bulk_delete(self, request):
        """Delete multiple snapshots by IDs"""
        snapshot_ids = request.data.get('snapshot_ids', [])
        if not snapshot_ids:
            return Response(
                {'error': 'No snapshot IDs provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        deleted_count = self.get_queryset().filter(id__in=snapshot_ids).delete()[0]
        return Response({
            'message': f'Deleted {deleted_count} report snapshots',
            'deleted_count': deleted_count
        })


class ReportTemplateViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for report templates
    """
    serializer_class = ReportTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter templates by user"""
        return ReportTemplate.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Automatically set user when creating"""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def generate_from_template(self, request, pk=None):
        """Generate reports based on template configuration"""
        template = self.get_object()
        
        # Get period from request or use defaults
        period_start = request.data.get('period_start')
        period_end = request.data.get('period_end')
        
        if not period_start or not period_end:
            today = date.today()
            if template.frequency == 'monthly':
                period_start = today.replace(day=1)
                period_end = today
            elif template.frequency == 'weekly':
                period_start = today - timedelta(days=today.weekday())
                period_end = today
            else:
                period_start = today
                period_end = today
        else:
            period_start = datetime.strptime(period_start, '%Y-%m-%d').date()
            period_end = datetime.strptime(period_end, '%Y-%m-%d').date()
        
        try:
            generator = ReportGenerator(request.user)
            generated_reports = {}
            
            for report_type in template.report_types:
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
                    continue
                
                generated_reports[report_type] = report_data
                
                # Cache the report
                ReportCache.cache_report(request.user, report_type, period_start, period_end, report_data)
            
            return Response({
                'template_name': template.name,
                'period_start': period_start,
                'period_end': period_end,
                'reports': generated_reports,
                'generated_at': timezone.now()
            })
            
        except Exception as e:
            logger.error(f"Error generating reports from template: {str(e)}")
            return Response(
                {'error': 'Error generating reports from template'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BusinessMetricViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for business metrics
    """
    serializer_class = BusinessMetricSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter metrics by user with optional filtering"""
        queryset = BusinessMetric.objects.filter(user=self.request.user)
        
        # Filter by metric type
        metric_type = self.request.query_params.get('metric_type')
        if metric_type:
            queryset = queryset.filter(metric_type=metric_type)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date and end_date:
            queryset = queryset.filter(
                metric_date__range=[start_date, end_date]
            )
        
        return queryset.order_by('-metric_date')
    
    def perform_create(self, serializer):
        """Automatically set user when creating"""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def latest_metrics(self, request):
        """Get the latest value for each metric type"""
        latest_metrics = []
        
        for metric_type, _ in BusinessMetric.METRIC_TYPES:
            latest_metric = self.get_queryset().filter(
                metric_type=metric_type
            ).first()
            
            if latest_metric:
                latest_metrics.append(latest_metric)
        
        serializer = self.get_serializer(latest_metrics, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def metric_trends(self, request):
        """Get trend data for specific metrics"""
        metric_type = request.query_params.get('metric_type')
        if not metric_type:
            return Response(
                {'error': 'metric_type parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Default to last 12 months
        end_date = date.today()
        start_date = end_date - timedelta(days=365)
        
        if 'start_date' in request.query_params:
            start_date = datetime.strptime(request.query_params['start_date'], '%Y-%m-%d').date()
        if 'end_date' in request.query_params:
            end_date = datetime.strptime(request.query_params['end_date'], '%Y-%m-%d').date()
        
        metrics = self.get_queryset().filter(
            metric_type=metric_type,
            metric_date__range=[start_date, end_date]
        ).order_by('metric_date')
        
        serializer = self.get_serializer(metrics, many=True)
        return Response({
            'metric_type': metric_type,
            'period_start': start_date,
            'period_end': end_date,
            'trend_data': serializer.data
        })


# ===============================
# Analytics Dashboard View
# ===============================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
@ratelimit(key='user', rate='10/m', method='GET')
def analytics_dashboard(request):
    """
    Comprehensive analytics dashboard with key metrics
    """
    try:
        today = date.today()
        current_month_start = today.replace(day=1)
        
        # Previous month for comparison
        prev_month_end = current_month_start - timedelta(days=1)
        prev_month_start = prev_month_end.replace(day=1)
        
        generator = ReportGenerator(request.user)
        
        # Current month reports
        current_pl = generator.generate_profit_loss_report(current_month_start, today)
        current_tax = generator.generate_tax_summary_report(current_month_start, today)
        current_overview = generator.generate_business_overview_report(current_month_start, today)
        
        # Previous month for comparison
        prev_pl = generator.generate_profit_loss_report(prev_month_start, prev_month_end)
        
        # Calculate growth rates
        revenue_growth = Decimal('0.00')
        profit_growth = Decimal('0.00')
        
        if prev_pl['total_income'] > 0:
            revenue_growth = ((current_pl['total_income'] - prev_pl['total_income']) / prev_pl['total_income'] * 100)
        
        if prev_pl['net_profit'] > 0:
            profit_growth = ((current_pl['net_profit'] - prev_pl['net_profit']) / prev_pl['net_profit'] * 100)
        
        # Get latest business metrics
        latest_metrics = {}
        for metric_type, _ in BusinessMetric.METRIC_TYPES:
            latest_metric = BusinessMetric.objects.filter(
                user=request.user,
                metric_type=metric_type
            ).first()
            
            if latest_metric:
                latest_metrics[metric_type] = BusinessMetricSerializer(latest_metric).data
        
        # Sales trend for last 6 months
        six_months_ago = today - timedelta(days=180)
        sales_trend = generator.generate_sales_trend_report(six_months_ago, today, 'monthly')
        
        return Response({
            'dashboard_date': today,
            'current_month': {
                'profit_loss': current_pl,
                'tax_summary': current_tax,
                'business_overview': current_overview
            },
            'growth_metrics': {
                'revenue_growth': revenue_growth,
                'profit_growth': profit_growth
            },
            'latest_business_metrics': latest_metrics,
            'sales_trend_6months': sales_trend,
            'generated_at': timezone.now()
        })
        
    except Exception as e:
        logger.error(f"Error generating analytics dashboard: {str(e)}")
        return Response(
            {'error': 'Error generating analytics dashboard'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
