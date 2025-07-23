from rest_framework import serializers
from .models import ServiceCategory, Service, WorkRecord
from employees.models import Employee


class ServiceCategorySerializer(serializers.ModelSerializer):
    services_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ServiceCategory
        fields = ['id', 'name', 'description', 'services_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_services_count(self, obj):
        return obj.services.filter(is_active=True).count()


class ServiceSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    pricing_type_display = serializers.CharField(source='get_pricing_type_display', read_only=True)
    price_display = serializers.CharField(read_only=True)
    
    class Meta:
        model = Service
        fields = [
            'id', 'name', 'category', 'category_name', 'pricing_type', 
            'pricing_type_display', 'hourly_rate', 'fixed_price', 
            'price_display', 'description', 'is_active', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, data):
        """Validate that correct pricing field is provided"""
        pricing_type = data.get('pricing_type')
        hourly_rate = data.get('hourly_rate')
        fixed_price = data.get('fixed_price')
        
        if pricing_type == 'hourly' and not hourly_rate:
            raise serializers.ValidationError("Hourly rate is required for hourly services")
        elif pricing_type == 'fixed' and not fixed_price:
            raise serializers.ValidationError("Fixed price is required for fixed-price services")
        
        return data


class ServiceCreateSerializer(ServiceSerializer):
    """Serializer for creating services"""
    
    class Meta(ServiceSerializer.Meta):
        fields = [
            'name', 'category', 'pricing_type', 'hourly_rate', 
            'fixed_price', 'description', 'is_active'
        ]


class ServiceListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing services"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    price_display = serializers.CharField(read_only=True)
    
    class Meta:
        model = Service
        fields = ['id', 'name', 'category_name', 'pricing_type', 'price_display', 'is_active']


class WorkRecordSerializer(serializers.ModelSerializer):
    worker_name = serializers.CharField(source='get_worker_name', read_only=True)
    worker_display = serializers.CharField(read_only=True)
    service_name = serializers.CharField(source='service.name', read_only=True)
    employee_name = serializers.CharField(source='employee.employee_name', read_only=True)
    worker_type_display = serializers.CharField(source='get_worker_type_display', read_only=True)
    
    class Meta:
        model = WorkRecord
        fields = [
            'id', 'worker_type', 'worker_type_display', 'employee', 
            'employee_name', 'owner_name', 'worker_name', 'worker_display',
            'service', 'service_name', 'date_of_work', 'hours_worked', 
            'quantity', 'total_amount', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'total_amount', 'created_at', 'updated_at']
    
    def validate(self, data):
        """Validate work record data"""
        worker_type = data.get('worker_type')
        employee = data.get('employee')
        owner_name = data.get('owner_name')
        service = data.get('service')
        hours_worked = data.get('hours_worked')
        quantity = data.get('quantity', 1)
        
        # Validate worker information
        if worker_type == 'employee' and not employee:
            raise serializers.ValidationError("Employee must be selected for employee work records")
        elif worker_type == 'owner' and not owner_name:
            raise serializers.ValidationError("Owner name is required for owner work records")
        
        # Validate work details based on service pricing type
        if service:
            if service.pricing_type == 'hourly' and not hours_worked:
                raise serializers.ValidationError("Hours worked is required for hourly services")
            elif service.pricing_type == 'fixed' and quantity < 1:
                raise serializers.ValidationError("Quantity must be at least 1 for fixed-price services")
        
        return data


class WorkRecordCreateSerializer(WorkRecordSerializer):
    """Serializer for creating work records"""
    
    class Meta(WorkRecordSerializer.Meta):
        fields = [
            'worker_type', 'employee', 'owner_name', 'service', 
            'date_of_work', 'hours_worked', 'quantity', 'notes'
        ]


class WorkRecordListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing work records"""
    worker_name = serializers.CharField(source='get_worker_name', read_only=True)
    service_name = serializers.CharField(source='service.name', read_only=True)
    
    class Meta:
        model = WorkRecord
        fields = [
            'id', 'worker_name', 'service_name', 'date_of_work', 
            'total_amount', 'worker_type'
        ]


class EmployeeWorkSummarySerializer(serializers.Serializer):
    """Serializer for employee work performance summary"""
    employee_id = serializers.CharField()
    employee_name = serializers.CharField()
    total_hours = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_earnings = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_tasks = serializers.IntegerField()
    services_performed = serializers.ListField(child=serializers.CharField())


class ServiceReportSerializer(serializers.Serializer):
    """Serializer for service performance reports"""
    service_name = serializers.CharField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_tasks = serializers.IntegerField()
    total_hours = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    average_per_task = serializers.DecimalField(max_digits=10, decimal_places=2)
