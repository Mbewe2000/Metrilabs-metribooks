from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import Employee
from .serializers import (
    EmployeeSerializer, 
    EmployeeCreateSerializer, 
    EmployeeListSerializer
)


class EmployeeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing employees
    Provides CRUD operations for Employee model
    """
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['employment_type', 'is_active']
    search_fields = ['employee_id', 'employee_name', 'phone_number']
    ordering_fields = ['employee_name', 'date_hired', 'pay']
    ordering = ['employee_name']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return EmployeeCreateSerializer
        elif self.action == 'list':
            return EmployeeListSerializer
        return EmployeeSerializer
    
    def get_queryset(self):
        """Filter queryset based on query parameters"""
        queryset = Employee.objects.all()
        
        # Filter by employment type
        employment_type = self.request.query_params.get('employment_type', None)
        if employment_type:
            queryset = queryset.filter(employment_type=employment_type)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            is_active_bool = is_active.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(is_active=is_active_bool)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def active_employees(self, request):
        """Get all active employees"""
        active_employees = Employee.objects.filter(is_active=True)
        serializer = EmployeeListSerializer(active_employees, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def full_time_employees(self, request):
        """Get all full-time employees"""
        full_time_employees = Employee.objects.filter(employment_type='full_time')
        serializer = EmployeeListSerializer(full_time_employees, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def part_time_employees(self, request):
        """Get all part-time employees"""
        part_time_employees = Employee.objects.filter(employment_type='part_time')
        serializer = EmployeeListSerializer(part_time_employees, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'])
    def deactivate(self, request, pk=None):
        """Deactivate an employee"""
        employee = self.get_object()
        employee.is_active = False
        employee.save()
        serializer = self.get_serializer(employee)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'])
    def activate(self, request, pk=None):
        """Activate an employee"""
        employee = self.get_object()
        employee.is_active = True
        employee.save()
        serializer = self.get_serializer(employee)
        return Response(serializer.data)
