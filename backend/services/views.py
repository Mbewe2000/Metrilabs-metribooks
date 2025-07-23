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

from .models import ServiceCategory, Service, Worker, ServiceRecord, WorkerPerformance
from .serializers import (
    ServiceCategorySerializer,
    ServiceSerializer,
    ServiceCreateUpdateSerializer,
    WorkerSerializer,
    WorkerCreateUpdateSerializer,
    ServiceRecordSerializer,
    ServiceRecordCreateUpdateSerializer,
    ServiceRecordSummarySerializer,
    WorkerPerformanceSerializer,
    DashboardSummarySerializer
)

# Get logger
logger = logging.getLogger('services')


# ===============================
# Service Category Views
# ===============================

class ServiceCategoryListView(generics.ListAPIView):
    """List all service categories"""
    queryset = ServiceCategory.objects.all()
    serializer_class = ServiceCategorySerializer
    permission_classes = [permissions.IsAuthenticated]


# ===============================
# Service Management Views
# ===============================

class ServiceListView(generics.ListAPIView):
    """List all services for the authenticated user"""
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Service.objects.filter(user=self.request.user).select_related('category')
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__name=category)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Filter by pricing type
        pricing_type = self.request.query_params.get('pricing_type')
        if pricing_type:
            queryset = queryset.filter(pricing_type=pricing_type)
        
        # Search by name
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset.order_by('name')


class ServiceCreateView(generics.CreateAPIView):
    """Create a new service"""
    serializer_class = ServiceCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @method_decorator(ratelimit(key='user', rate='50/h', method='POST'))
    def post(self, request, *args, **kwargs):
        try:
            response = super().create(request, *args, **kwargs)
            
            logger.info(f"Service created by user: {request.user.email}")
            return Response({
                'success': True,
                'message': 'Service created successfully',
                'data': response.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error creating service for user {request.user.email}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error creating service',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ServiceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a service"""
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Service.objects.filter(user=self.request.user).select_related('category')
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ServiceCreateUpdateSerializer
        return ServiceSerializer
    
    @method_decorator(ratelimit(key='user', rate='100/h', method=['PUT', 'PATCH']))
    def update(self, request, *args, **kwargs):
        from django.http import Http404
        from django.core.exceptions import ValidationError
        
        try:
            response = super().update(request, *args, **kwargs)
            logger.info(f"Service updated by user: {request.user.email}")
            return Response({
                'success': True,
                'message': 'Service updated successfully',
                'data': response.data
            })
        except Http404:
            # Re-raise Http404 to let Django handle it properly
            raise
        except ValidationError as e:
            logger.warning(f"Validation error updating service for user {request.user.email}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Validation error',
                'errors': e.message_dict if hasattr(e, 'message_dict') else str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error updating service for user {request.user.email}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error updating service',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def destroy(self, request, *args, **kwargs):
        from django.http import Http404
        
        try:
            instance = self.get_object()
            service_name = instance.name
            
            # Check if service has associated records
            if ServiceRecord.objects.filter(service=instance).exists():
                return Response({
                    'success': False,
                    'message': 'Cannot delete service with existing service records'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            instance.delete()
            
            logger.info(f"Service '{service_name}' deleted by user: {request.user.email}")
            return Response({
                'success': True,
                'message': 'Service deleted successfully'
            })
        except Http404:
            raise
        except Exception as e:
            logger.error(f"Error deleting service for user {request.user.email}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error deleting service',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ===============================
# Worker Management Views
# ===============================

class WorkerListView(generics.ListAPIView):
    """List all workers for the authenticated user"""
    serializer_class = WorkerSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Worker.objects.filter(user=self.request.user).prefetch_related('services')
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Filter by service capability
        service = self.request.query_params.get('service')
        if service:
            queryset = queryset.filter(services__name__icontains=service)
        
        # Search by name
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset.order_by('-is_owner', 'name')


class WorkerCreateView(generics.CreateAPIView):
    """Create a new worker"""
    serializer_class = WorkerCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @method_decorator(ratelimit(key='user', rate='30/h', method='POST'))
    def post(self, request, *args, **kwargs):
        try:
            response = super().create(request, *args, **kwargs)
            
            logger.info(f"Worker created by user: {request.user.email}")
            return Response({
                'success': True,
                'message': 'Worker created successfully',
                'data': response.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error creating worker for user {request.user.email}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error creating worker',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WorkerDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a worker"""
    serializer_class = WorkerSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Worker.objects.filter(user=self.request.user).prefetch_related('services')
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return WorkerCreateUpdateSerializer
        return WorkerSerializer
    
    def update(self, request, *args, **kwargs):
        from django.http import Http404
        from django.core.exceptions import ValidationError
        
        try:
            response = super().update(request, *args, **kwargs)
            logger.info(f"Worker updated by user: {request.user.email}")
            return Response({
                'success': True,
                'message': 'Worker updated successfully',
                'data': response.data
            })
        except Http404:
            # Re-raise Http404 to let Django handle it properly
            raise
        except ValidationError as e:
            logger.warning(f"Validation error updating worker for user {request.user.email}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Validation error',
                'errors': e.message_dict if hasattr(e, 'message_dict') else str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error updating worker for user {request.user.email}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error updating worker',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def destroy(self, request, *args, **kwargs):
        from django.http import Http404
        
        try:
            instance = self.get_object()
            worker_name = instance.name
            
            # Check if worker has associated records
            if ServiceRecord.objects.filter(worker=instance).exists():
                return Response({
                    'success': False,
                    'message': 'Cannot delete worker with existing service records'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            instance.delete()
            
            logger.info(f"Worker '{worker_name}' deleted by user: {request.user.email}")
            return Response({
                'success': True,
                'message': 'Worker deleted successfully'
            })
        except Http404:
            raise
        except Exception as e:
            logger.error(f"Error deleting worker for user {request.user.email}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error deleting worker',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ===============================
# Service Record Views
# ===============================

class ServiceRecordListView(generics.ListAPIView):
    """List all service records for the authenticated user"""
    serializer_class = ServiceRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = ServiceRecord.objects.filter(user=self.request.user).select_related(
            'worker', 'service'
        )
        
        # Filter by worker
        worker = self.request.query_params.get('worker')
        if worker:
            queryset = queryset.filter(worker__id=worker)
        
        # Filter by service
        service = self.request.query_params.get('service')
        if service:
            queryset = queryset.filter(service__id=service)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date_performed__gte=start_date)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date_performed__lte=end_date)
            except ValueError:
                pass
        
        # Filter by payment status
        payment_status = self.request.query_params.get('payment_status')
        if payment_status:
            queryset = queryset.filter(payment_status=payment_status)
        
        # Search by customer name or reference number
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(customer_name__icontains=search) | 
                Q(reference_number__icontains=search) |
                Q(notes__icontains=search)
            )
        
        return queryset.order_by('-date_performed', '-created_at')


class ServiceRecordCreateView(generics.CreateAPIView):
    """Create a new service record"""
    serializer_class = ServiceRecordCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @method_decorator(ratelimit(key='user', rate='100/h', method='POST'))
    def post(self, request, *args, **kwargs):
        try:
            response = super().create(request, *args, **kwargs)
            
            logger.info(f"Service record created by user: {request.user.email}")
            return Response({
                'success': True,
                'message': 'Service record created successfully',
                'data': response.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error creating service record for user {request.user.email}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error creating service record',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ServiceRecordDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a service record"""
    serializer_class = ServiceRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return ServiceRecord.objects.filter(user=self.request.user).select_related(
            'worker', 'service'
        )
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ServiceRecordCreateUpdateSerializer
        return ServiceRecordSerializer
    
    def update(self, request, *args, **kwargs):
        try:
            response = super().update(request, *args, **kwargs)
            logger.info(f"Service record updated by user: {request.user.email}")
            return Response({
                'success': True,
                'message': 'Service record updated successfully',
                'data': response.data
            })
        except Exception as e:
            logger.error(f"Error updating service record for user {request.user.email}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error updating service record',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def destroy(self, request, *args, **kwargs):
        from django.http import Http404
        
        try:
            instance = self.get_object()
            instance.delete()
            
            logger.info(f"Service record deleted by user: {request.user.email}")
            return Response({
                'success': True,
                'message': 'Service record deleted successfully'
            })
        except Http404:
            raise
        except Exception as e:
            logger.error(f"Error deleting service record for user {request.user.email}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error deleting service record',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ===============================
# Payment Management Views
# ===============================

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@ratelimit(key='user', rate='50/h', method='POST')
def update_payment(request, record_id):
    """Update payment for a service record"""
    try:
        record = get_object_or_404(
            ServiceRecord,
            id=record_id,
            user=request.user
        )
        
        amount_paid = request.data.get('amount_paid')
        
        if amount_paid is None:
            return Response({
                'success': False,
                'message': 'Amount paid is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            amount_paid = Decimal(str(amount_paid))
        except (ValueError, TypeError):
            return Response({
                'success': False,
                'message': 'Invalid amount format'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if amount_paid < 0:
            return Response({
                'success': False,
                'message': 'Amount paid cannot be negative'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if amount_paid > record.total_amount:
            return Response({
                'success': False,
                'message': 'Amount paid cannot exceed total amount'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        record.amount_paid = amount_paid
        record.update_payment_status()
        record.save()
        
        logger.info(f"Payment updated for service record {record_id} by user: {request.user.email}")
        
        return Response({
            'success': True,
            'message': 'Payment updated successfully',
            'data': {
                'record_id': record.id,
                'amount_paid': record.amount_paid,
                'remaining_balance': record.remaining_balance,
                'payment_status': record.payment_status,
                'is_fully_paid': record.is_fully_paid
            }
        })
        
    except Exception as e:
        logger.error(f"Error updating payment for user {request.user.email}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Error updating payment',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ===============================
# Reports and Analytics Views
# ===============================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard(request):
    """Get dashboard summary for services"""
    try:
        user = request.user
        today = timezone.now().date()
        month_start = today.replace(day=1)
        
        # Basic counts
        total_services = Service.objects.filter(user=user, is_active=True).count()
        total_workers = Worker.objects.filter(user=user).count()
        active_workers = Worker.objects.filter(user=user, is_active=True).count()
        
        # Today's stats
        today_records = ServiceRecord.objects.filter(user=user, date_performed=today)
        today_stats = today_records.aggregate(
            count=Count('id'),
            revenue=Sum('total_amount') or Decimal('0.00'),
            hours=Sum('hours_worked') or Decimal('0.00')
        )
        
        # This month's stats
        month_records = ServiceRecord.objects.filter(
            user=user, 
            date_performed__gte=month_start
        )
        month_stats = month_records.aggregate(
            count=Count('id'),
            revenue=Sum('total_amount') or Decimal('0.00'),
            hours=Sum('hours_worked') or Decimal('0.00')
        )
        
        # Payment stats
        pending_payments = ServiceRecord.objects.filter(
            user=user,
            payment_status__in=['pending', 'partially_paid']
        ).aggregate(
            total=Sum(F('total_amount') - F('amount_paid'))
        )['total'] or Decimal('0.00')
        
        overdue_payments = ServiceRecord.objects.filter(
            user=user,
            payment_status='pending',
            date_performed__lt=today - timedelta(days=30)
        ).count()
        
        # Top workers this month
        top_workers = list(
            month_records.values('worker__name')
            .annotate(
                revenue=Sum('total_amount'),
                hours=Sum('hours_worked'),
                services=Count('id')
            )
            .order_by('-revenue')[:5]
        )
        
        # Top services this month
        top_services = list(
            month_records.values('service__name')
            .annotate(
                revenue=Sum('total_amount'),
                count=Count('id')
            )
            .order_by('-count')[:5]
        )
        
        dashboard_data = {
            'total_services': total_services,
            'total_workers': total_workers,
            'active_workers': active_workers,
            'today_records': today_stats['count'],
            'today_revenue': today_stats['revenue'],
            'today_hours': today_stats['hours'],
            'month_records': month_stats['count'],
            'month_revenue': month_stats['revenue'],
            'month_hours': month_stats['hours'],
            'pending_payments': pending_payments,
            'overdue_payments': overdue_payments,
            'top_workers': top_workers,
            'top_services': top_services
        }
        
        serializer = DashboardSummarySerializer(dashboard_data)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
        
    except Exception as e:
        logger.error(f"Error generating dashboard for user {request.user.email}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Error generating dashboard',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def service_records_summary(request):
    """Get summary of service records with filtering"""
    try:
        user = request.user
        
        # Get filters from query parameters
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        worker_id = request.GET.get('worker')
        service_id = request.GET.get('service')
        
        # Build base queryset
        queryset = ServiceRecord.objects.filter(user=user)
        
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date_performed__gte=start_date)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date_performed__lte=end_date)
            except ValueError:
                pass
        
        if worker_id:
            queryset = queryset.filter(worker__id=worker_id)
        
        if service_id:
            queryset = queryset.filter(service__id=service_id)
        
        # Calculate summary statistics
        summary_stats = queryset.aggregate(
            total_records=Count('id'),
            total_revenue=Sum('total_amount') or Decimal('0.00'),
            total_hours=Sum('hours_worked') or Decimal('0.00'),
            average_hourly_rate=Avg('hourly_rate_used') or Decimal('0.00'),
            pending_payments=Sum(
                F('total_amount') - F('amount_paid'),
                filter=Q(payment_status__in=['pending', 'partially_paid'])
            ) or Decimal('0.00')
        )
        
        # Breakdown by worker
        by_worker = list(
            queryset.values('worker__name')
            .annotate(
                total_revenue=Sum('total_amount'),
                total_hours=Sum('hours_worked'),
                service_count=Count('id')
            )
            .order_by('-total_revenue')
        )
        
        # Breakdown by service
        by_service = list(
            queryset.values('service__name')
            .annotate(
                total_revenue=Sum('total_amount'),
                total_hours=Sum('hours_worked'),
                service_count=Count('id')
            )
            .order_by('-service_count')
        )
        
        summary_data = {
            **summary_stats,
            'by_worker': by_worker,
            'by_service': by_service
        }
        
        serializer = ServiceRecordSummarySerializer(summary_data)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
        
    except Exception as e:
        logger.error(f"Error generating service records summary for user {request.user.email}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Error generating summary',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def worker_performance_report(request):
    """Get worker performance report"""
    try:
        user = request.user
        year = request.GET.get('year', timezone.now().year)
        month = request.GET.get('month')
        
        try:
            year = int(year)
        except (ValueError, TypeError):
            year = timezone.now().year
        
        queryset = WorkerPerformance.objects.filter(user=user, year=year)
        
        if month:
            try:
                month = int(month)
                queryset = queryset.filter(month=month)
            except (ValueError, TypeError):
                pass
        
        # Generate performance records for current month if not exists
        current_date = timezone.now().date()
        if not month or (month == current_date.month and year == current_date.year):
            WorkerPerformance.generate_for_period(user, current_date.year, current_date.month)
            # Refresh queryset
            queryset = WorkerPerformance.objects.filter(user=user, year=year)
            if month:
                queryset = queryset.filter(month=month)
        
        performance_data = queryset.order_by('-total_revenue_generated')
        serializer = WorkerPerformanceSerializer(performance_data, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
        
    except Exception as e:
        logger.error(f"Error generating worker performance report for user {request.user.email}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Error generating performance report',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
