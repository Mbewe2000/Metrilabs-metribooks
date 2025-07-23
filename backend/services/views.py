from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from datetime import datetime, timedelta
from .models import ServiceCategory, Service, WorkRecord
from .serializers import (
    ServiceCategorySerializer,
    ServiceSerializer, ServiceCreateSerializer, ServiceListSerializer,
    WorkRecordSerializer, WorkRecordCreateSerializer, WorkRecordListSerializer,
    EmployeeWorkSummarySerializer, ServiceReportSerializer
)
from employees.models import Employee


class ServiceCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for managing service categories"""
    queryset = ServiceCategory.objects.all()
    serializer_class = ServiceCategorySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class ServiceViewSet(viewsets.ModelViewSet):
    """ViewSet for managing services"""
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'hourly_rate', 'fixed_price']
    ordering = ['name']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return ServiceCreateSerializer
        elif self.action == 'list':
            return ServiceListSerializer
        return ServiceSerializer
    
    def get_queryset(self):
        """Filter queryset based on query parameters"""
        queryset = Service.objects.all()
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            is_active_bool = is_active.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(is_active=is_active_bool)
        
        # Filter by pricing type
        pricing_type = self.request.query_params.get('pricing_type', None)
        if pricing_type:
            queryset = queryset.filter(pricing_type=pricing_type)
        
        # Filter by category
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category_id=category)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def active_services(self, request):
        """Get all active services"""
        active_services = Service.objects.filter(is_active=True)
        serializer = ServiceListSerializer(active_services, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def hourly_services(self, request):
        """Get all hourly services"""
        hourly_services = Service.objects.filter(pricing_type='hourly', is_active=True)
        serializer = ServiceListSerializer(hourly_services, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def fixed_price_services(self, request):
        """Get all fixed-price services"""
        fixed_services = Service.objects.filter(pricing_type='fixed', is_active=True)
        serializer = ServiceListSerializer(fixed_services, many=True)
        return Response(serializer.data)


class WorkRecordViewSet(viewsets.ModelViewSet):
    """ViewSet for managing work records"""
    queryset = WorkRecord.objects.all()
    serializer_class = WorkRecordSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['service__name', 'employee__employee_name', 'owner_name', 'notes']
    ordering_fields = ['date_of_work', 'total_amount', 'created_at']
    ordering = ['-date_of_work', '-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return WorkRecordCreateSerializer
        elif self.action == 'list':
            return WorkRecordListSerializer
        return WorkRecordSerializer
    
    def get_queryset(self):
        """Filter queryset based on query parameters"""
        queryset = WorkRecord.objects.select_related('service', 'employee').all()
        
        # Filter by worker type
        worker_type = self.request.query_params.get('worker_type', None)
        if worker_type:
            queryset = queryset.filter(worker_type=worker_type)
        
        # Filter by employee
        employee_id = self.request.query_params.get('employee', None)
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        
        # Filter by service
        service_id = self.request.query_params.get('service', None)
        if service_id:
            queryset = queryset.filter(service_id=service_id)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date_of_work__gte=start_date)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date_of_work__lte=end_date)
            except ValueError:
                pass
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def today_records(self, request):
        """Get today's work records"""
        today = timezone.now().date()
        today_records = WorkRecord.objects.filter(date_of_work=today)
        serializer = WorkRecordListSerializer(today_records, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def this_week_records(self, request):
        """Get this week's work records"""
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        week_records = WorkRecord.objects.filter(date_of_work__gte=week_start)
        serializer = WorkRecordListSerializer(week_records, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def employee_summary(self, request):
        """Get work summary by employee"""
        # Get date range from query params
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        queryset = WorkRecord.objects.filter(worker_type='employee')
        
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date_of_work__gte=start_date)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date_of_work__lte=end_date)
            except ValueError:
                pass
        
        # Group by employee and calculate summaries
        employee_summaries = []
        for employee in Employee.objects.filter(is_active=True):
            employee_records = queryset.filter(employee=employee)
            
            if employee_records.exists():
                total_hours = employee_records.aggregate(
                    total=Sum('hours_worked')
                )['total'] or 0
                
                total_earnings = employee_records.aggregate(
                    total=Sum('total_amount')
                )['total'] or 0
                
                total_tasks = employee_records.count()
                
                services_performed = list(
                    employee_records.values_list('service__name', flat=True).distinct()
                )
                
                employee_summaries.append({
                    'employee_id': employee.employee_id,
                    'employee_name': employee.employee_name,
                    'total_hours': total_hours,
                    'total_earnings': total_earnings,
                    'total_tasks': total_tasks,
                    'services_performed': services_performed
                })
        
        serializer = EmployeeWorkSummarySerializer(employee_summaries, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def service_report(self, request):
        """Get performance report by service"""
        # Get date range from query params
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        queryset = WorkRecord.objects.all()
        
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date_of_work__gte=start_date)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date_of_work__lte=end_date)
            except ValueError:
                pass
        
        # Group by service and calculate summaries
        service_reports = []
        for service in Service.objects.filter(is_active=True):
            service_records = queryset.filter(service=service)
            
            if service_records.exists():
                total_revenue = service_records.aggregate(
                    total=Sum('total_amount')
                )['total'] or 0
                
                total_tasks = service_records.count()
                
                total_hours = service_records.aggregate(
                    total=Sum('hours_worked')
                )['total']
                
                average_per_task = total_revenue / total_tasks if total_tasks > 0 else 0
                
                service_reports.append({
                    'service_name': service.name,
                    'total_revenue': total_revenue,
                    'total_tasks': total_tasks,
                    'total_hours': total_hours,
                    'average_per_task': average_per_task
                })
        
        # Sort by total revenue descending
        service_reports.sort(key=lambda x: x['total_revenue'], reverse=True)
        
        serializer = ServiceReportSerializer(service_reports, many=True)
        return Response(serializer.data)
