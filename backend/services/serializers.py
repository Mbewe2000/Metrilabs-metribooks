from rest_framework import serializers
from decimal import Decimal
from django.utils import timezone
from .models import ServiceCategory, Service, Worker, ServiceRecord, WorkerPerformance


class ServiceCategorySerializer(serializers.ModelSerializer):
    """Serializer for service categories"""
    
    class Meta:
        model = ServiceCategory
        fields = ['id', 'name', 'description', 'created_at']
        read_only_fields = ['created_at']


class ServiceSerializer(serializers.ModelSerializer):
    """Serializer for viewing services"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    display_price = serializers.CharField(source='get_display_price', read_only=True)
    
    class Meta:
        model = Service
        fields = [
            'id', 'name', 'description', 'category', 'category_name',
            'pricing_type', 'hourly_rate', 'fixed_price', 'display_price',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ServiceCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating services"""
    
    class Meta:
        model = Service
        fields = [
            'id', 'name', 'description', 'category', 'pricing_type',
            'hourly_rate', 'fixed_price', 'is_active'
        ]
    
    def validate(self, data):
        """Validate pricing based on pricing type"""
        pricing_type = data.get('pricing_type')
        hourly_rate = data.get('hourly_rate')
        fixed_price = data.get('fixed_price')
        
        if pricing_type == 'hourly' and not hourly_rate:
            raise serializers.ValidationError("Hourly rate is required for hourly pricing")
        
        if pricing_type == 'fixed' and not fixed_price:
            raise serializers.ValidationError("Fixed price is required for fixed pricing")
        
        if pricing_type == 'both' and not (hourly_rate and fixed_price):
            raise serializers.ValidationError("Both hourly rate and fixed price are required for 'both' pricing type")
        
        # Validate positive values
        if hourly_rate and hourly_rate <= 0:
            raise serializers.ValidationError("Hourly rate must be greater than 0")
        
        if fixed_price and fixed_price <= 0:
            raise serializers.ValidationError("Fixed price must be greater than 0")
        
        return data
    
    def create(self, validated_data):
        """Create service with user from request context"""
        validated_data['user'] = self.context['request'].user
        return Service.objects.create(**validated_data)


class WorkerSerializer(serializers.ModelSerializer):
    """Serializer for viewing workers"""
    services_list = serializers.CharField(source='get_services_list', read_only=True)
    services_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Worker
        fields = [
            'id', 'name', 'employee_id', 'phone', 'email',
            'is_owner', 'is_active', 'services', 'services_list', 'services_count',
            'hired_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_services_count(self, obj):
        """Get count of services this worker can perform"""
        return obj.services.count()


class WorkerCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating workers"""
    
    class Meta:
        model = Worker
        fields = [
            'id', 'name', 'employee_id', 'phone', 'email',
            'is_owner', 'is_active', 'services', 'hired_date'
        ]
    
    def validate_services(self, value):
        """Validate that services belong to the user"""
        user = self.context['request'].user
        for service in value:
            if service.user != user:
                raise serializers.ValidationError(f"Service '{service.name}' does not belong to you")
        return value
    
    def create(self, validated_data):
        """Create worker with user from request context"""
        services = validated_data.pop('services', [])
        validated_data['user'] = self.context['request'].user
        
        worker = Worker.objects.create(**validated_data)
        worker.services.set(services)
        return worker


class ServiceRecordSerializer(serializers.ModelSerializer):
    """Serializer for viewing service records"""
    worker_name = serializers.CharField(source='worker.name', read_only=True)
    service_name = serializers.CharField(source='service.name', read_only=True)
    remaining_balance = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        read_only=True
    )
    is_fully_paid = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = ServiceRecord
        fields = [
            'id', 'worker', 'worker_name', 'service', 'service_name',
            'date_performed', 'start_time', 'end_time', 'hours_worked',
            'used_fixed_price', 'hourly_rate_used', 'fixed_price_used',
            'total_amount', 'customer_name', 'notes', 'reference_number',
            'payment_status', 'amount_paid', 'remaining_balance', 'is_fully_paid',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ServiceRecordCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating service records"""
    
    class Meta:
        model = ServiceRecord
        fields = [
            'worker', 'service', 'date_performed', 'start_time', 'end_time',
            'hours_worked', 'used_fixed_price', 'hourly_rate_used', 'fixed_price_used',
            'total_amount', 'customer_name', 'notes', 'reference_number',
            'payment_status', 'amount_paid'
        ]
    
    def validate_worker(self, value):
        """Validate that worker belongs to the user"""
        user = self.context['request'].user
        if value.user != user:
            raise serializers.ValidationError("Worker does not belong to you")
        return value
    
    def validate_service(self, value):
        """Validate that service belongs to the user"""
        user = self.context['request'].user
        if value.user != user:
            raise serializers.ValidationError("Service does not belong to you")
        return value
    
    def validate(self, data):
        """Validate service record data"""
        worker = data.get('worker')
        service = data.get('service')
        used_fixed_price = data.get('used_fixed_price', False)
        hours_worked = data.get('hours_worked')
        hourly_rate_used = data.get('hourly_rate_used')
        fixed_price_used = data.get('fixed_price_used')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        # Validate worker can perform this service
        if worker and service and worker.services.exists():
            if service not in worker.services.all():
                raise serializers.ValidationError(
                    f"{worker.name} is not assigned to perform {service.name}"
                )
        
        # Validate pricing logic
        if not used_fixed_price and not hours_worked:
            # Check if we can calculate from start/end time
            if not (start_time and end_time):
                raise serializers.ValidationError(
                    "Hours worked is required when not using fixed pricing, or provide start and end times"
                )
        
        if used_fixed_price and not fixed_price_used:
            raise serializers.ValidationError("Fixed price is required when using fixed pricing")
        
        if not used_fixed_price and not hourly_rate_used:
            raise serializers.ValidationError("Hourly rate is required when not using fixed pricing")
        
        # Validate time logic
        if start_time and end_time and start_time >= end_time:
            # Allow overnight work, but validate that it makes sense
            pass  # We'll handle this in the model's calculate_hours_worked method
        
        return data
    
    def create(self, validated_data):
        """Create service record with user from request context"""
        validated_data['user'] = self.context['request'].user
        return ServiceRecord.objects.create(**validated_data)


class ServiceRecordSummarySerializer(serializers.Serializer):
    """Serializer for service record summaries"""
    total_records = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_hours = serializers.DecimalField(max_digits=10, decimal_places=2)
    average_hourly_rate = serializers.DecimalField(max_digits=10, decimal_places=2)
    pending_payments = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    # By worker breakdown
    by_worker = serializers.SerializerMethodField()
    
    # By service breakdown
    by_service = serializers.SerializerMethodField()
    
    def get_by_worker(self, obj):
        """Get breakdown by worker"""
        return obj.get('by_worker', [])
    
    def get_by_service(self, obj):
        """Get breakdown by service"""
        return obj.get('by_service', [])


class WorkerPerformanceSerializer(serializers.ModelSerializer):
    """Serializer for worker performance records"""
    worker_name = serializers.CharField(source='worker.name', read_only=True)
    month_name = serializers.SerializerMethodField()
    
    class Meta:
        model = WorkerPerformance
        fields = [
            'id', 'worker', 'worker_name', 'year', 'month', 'month_name',
            'total_hours_worked', 'total_services_performed', 'total_revenue_generated',
            'average_hourly_rate', 'services_breakdown', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_month_name(self, obj):
        """Get month name from month number"""
        months = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]
        return months[obj.month - 1] if 1 <= obj.month <= 12 else str(obj.month)


class DashboardSummarySerializer(serializers.Serializer):
    """Serializer for services dashboard summary"""
    total_services = serializers.IntegerField()
    total_workers = serializers.IntegerField()
    active_workers = serializers.IntegerField()
    
    # Today's stats
    today_records = serializers.IntegerField()
    today_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    today_hours = serializers.DecimalField(max_digits=10, decimal_places=2)
    
    # This month's stats
    month_records = serializers.IntegerField()
    month_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    month_hours = serializers.DecimalField(max_digits=10, decimal_places=2)
    
    # Payment stats
    pending_payments = serializers.DecimalField(max_digits=12, decimal_places=2)
    overdue_payments = serializers.IntegerField()
    
    # Top performers this month
    top_workers = serializers.ListSerializer(child=serializers.DictField())
    top_services = serializers.ListSerializer(child=serializers.DictField())
