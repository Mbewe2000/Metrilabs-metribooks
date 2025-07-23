from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q, Sum, Count, Avg, F
from django.utils import timezone
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from decimal import Decimal
from datetime import datetime, timedelta
import logging

from .models import Sale, SaleItem, SalesReport
from .serializers import (
    SaleSerializer,
    SaleCreateSerializer,
    SaleUpdateSerializer,
    SaleItemSerializer,
    SalesReportSerializer,
    DashboardSummarySerializer,
    SalesSummarySerializer
)

# Get logger
logger = logging.getLogger('sales')


# ===============================
# Sale Management Views
# ===============================

class SaleListView(generics.ListAPIView):
    """List all sales for the authenticated user"""
    serializer_class = SaleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Sale.objects.filter(user=self.request.user).select_related().prefetch_related('items')
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(sale_date__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(sale_date__date__lte=end_date)
        
        # Filter by payment method
        payment_method = self.request.query_params.get('payment_method')
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)
        
        # Filter by status
        sale_status = self.request.query_params.get('status')
        if sale_status:
            queryset = queryset.filter(status=sale_status)
        
        # Filter by customer
        customer = self.request.query_params.get('customer')
        if customer:
            queryset = queryset.filter(customer_name__icontains=customer)
        
        # Search by sale number
        sale_number = self.request.query_params.get('sale_number')
        if sale_number:
            queryset = queryset.filter(sale_number__icontains=sale_number)
        
        return queryset.order_by('-sale_date')


class SaleCreateView(generics.CreateAPIView):
    """Create a new sale"""
    serializer_class = SaleCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @method_decorator(ratelimit(key='user', rate='100/h', method='POST'))
    def post(self, request, *args, **kwargs):
        try:
            response = super().create(request, *args, **kwargs)
            
            logger.info(f"Sale created by user: {request.user.email}")
            return Response({
                'success': True,
                'message': 'Sale created successfully',
                'data': response.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error creating sale for user {request.user.email}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error creating sale',
                'errors': [str(e)]
            }, status=status.HTTP_400_BAD_REQUEST)


class SaleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a sale"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Sale.objects.filter(user=self.request.user).prefetch_related('items')
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return SaleUpdateSerializer
        return SaleSerializer
    
    def update(self, request, *args, **kwargs):
        try:
            response = super().update(request, *args, **kwargs)
            return Response({
                'success': True,
                'message': 'Sale updated successfully',
                'data': response.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error updating sale for user {request.user.email}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error updating sale',
                'errors': [str(e)]
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        try:
            sale = self.get_object()
            
            # Check if sale can be deleted (only allow deletion of pending/cancelled sales)
            if sale.status not in ['pending', 'cancelled']:
                return Response({
                    'success': False,
                    'message': 'Only pending or cancelled sales can be deleted',
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Delete the sale - inventory movements will be handled by signals
            sale.delete()
            
            return Response({
                'success': True,
                'message': 'Sale deleted successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error deleting sale for user {request.user.email}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error deleting sale',
                'errors': [str(e)]
            }, status=status.HTTP_400_BAD_REQUEST)


# ===============================
# Sale Items Views
# ===============================

class SaleItemListView(generics.ListAPIView):
    """List all sale items for a specific sale"""
    serializer_class = SaleItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        sale_id = self.kwargs.get('sale_id')
        sale = get_object_or_404(Sale, id=sale_id, user=self.request.user)
        return SaleItem.objects.filter(sale=sale)


# ===============================
# Reports and Analytics Views
# ===============================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard(request):
    """Sales dashboard with key metrics"""
    user = request.user
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    
    # Today's metrics
    today_sales = Sale.objects.filter(
        user=user,
        sale_date__date=today,
        status='completed'
    )
    today_count = today_sales.count()
    today_revenue = today_sales.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
    
    # This week's metrics
    week_sales = Sale.objects.filter(
        user=user,
        sale_date__date__gte=week_start,
        status='completed'
    )
    week_count = week_sales.count()
    week_revenue = week_sales.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
    
    # This month's metrics
    month_sales = Sale.objects.filter(
        user=user,
        sale_date__date__gte=month_start,
        status='completed'
    )
    month_count = month_sales.count()
    month_revenue = month_sales.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
    
    # Recent sales
    recent_sales = Sale.objects.filter(user=user).order_by('-sale_date')[:5]
    
    # Payment method breakdown (last 30 days)
    thirty_days_ago = today - timedelta(days=30)
    payment_breakdown = Sale.objects.filter(
        user=user,
        sale_date__date__gte=thirty_days_ago,
        status='completed'
    ).values('payment_method').annotate(
        count=Count('id'),
        total=Sum('total_amount')
    ).order_by('-total')
    
    # Top products (last 30 days)
    top_products = SaleItem.objects.filter(
        sale__user=user,
        sale__sale_date__date__gte=thirty_days_ago,
        sale__status='completed',
        item_type='product'
    ).values('product__name').annotate(
        quantity_sold=Sum('quantity'),
        revenue=Sum('total_price')
    ).order_by('-quantity_sold')[:5]
    
    # Top services (last 30 days)
    top_services = SaleItem.objects.filter(
        sale__user=user,
        sale__sale_date__date__gte=thirty_days_ago,
        sale__status='completed',
        item_type='service'
    ).values('service__name').annotate(
        quantity_sold=Sum('quantity'),
        revenue=Sum('total_price')
    ).order_by('-quantity_sold')[:5]
    
    dashboard_data = {
        'today_sales': today_count,
        'today_revenue': today_revenue,
        'this_week_sales': week_count,
        'this_week_revenue': week_revenue,
        'this_month_sales': month_count,
        'this_month_revenue': month_revenue,
        'recent_sales': SaleSerializer(recent_sales, many=True).data,
        'payment_methods': list(payment_breakdown),
        'top_products': list(top_products),
        'top_services': list(top_services),
    }
    
    return Response({
        'success': True,
        'data': dashboard_data
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def sales_summary(request):
    """Sales summary with filters"""
    user = request.user
    
    # Get date range from query params
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Default to last 30 days if no dates provided
    if not start_date:
        start_date = (timezone.now().date() - timedelta(days=30)).isoformat()
    if not end_date:
        end_date = timezone.now().date().isoformat()
    
    # Filter sales
    sales_queryset = Sale.objects.filter(
        user=user,
        sale_date__date__gte=start_date,
        sale_date__date__lte=end_date,
        status='completed'
    )
    
    # Calculate summary metrics
    summary_data = sales_queryset.aggregate(
        total_sales=Count('id'),
        total_revenue=Sum('total_amount'),
        total_discount=Sum('discount_amount'),
        total_tax=Sum('tax_amount'),
        average_sale=Avg('total_amount')
    )
    
    # Payment method breakdown
    payment_breakdown = sales_queryset.values('payment_method').annotate(
        count=Count('id'),
        total=Sum('total_amount')
    ).order_by('-total')
    
    # Daily breakdown
    daily_breakdown = sales_queryset.extra(
        select={'day': 'DATE(sale_date)'}
    ).values('day').annotate(
        count=Count('id'),
        total=Sum('total_amount')
    ).order_by('day')
    
    response_data = {
        'total_sales': summary_data['total_sales'] or 0,
        'total_revenue': summary_data['total_revenue'] or Decimal('0.00'),
        'total_discount': summary_data['total_discount'] or Decimal('0.00'),
        'total_tax': summary_data['total_tax'] or Decimal('0.00'),
        'average_sale_amount': summary_data['average_sale'] or Decimal('0.00'),
        'payment_breakdown': list(payment_breakdown),
        'period_breakdown': list(daily_breakdown),
    }
    
    return Response({
        'success': True,
        'data': response_data
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@ratelimit(key='user', rate='10/h', method='POST')
def generate_receipt(request, sale_id):
    """Generate receipt/invoice for a sale"""
    try:
        sale = get_object_or_404(Sale, id=sale_id, user=request.user)
        
        # Get user's business profile
        try:
            profile = request.user.profile
            business_name = profile.business_name
            business_city = profile.business_city
        except:
            business_name = "Your Business"
            business_city = "Lusaka"
        
        receipt_data = {
            'sale': SaleSerializer(sale).data,
            'business_info': {
                'name': business_name,
                'city': business_city,
                'generated_at': timezone.now().isoformat(),
            }
        }
        
        return Response({
            'success': True,
            'data': receipt_data
        })
        
    except Exception as e:
        logger.error(f"Error generating receipt for user {request.user.email}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Error generating receipt',
            'errors': [str(e)]
        }, status=status.HTTP_400_BAD_REQUEST)


# ===============================
# Sales Reports Views
# ===============================

class SalesReportListView(generics.ListAPIView):
    """List sales reports"""
    serializer_class = SalesReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return SalesReport.objects.filter(user=self.request.user).order_by('-period_end')
