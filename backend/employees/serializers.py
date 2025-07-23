from rest_framework import serializers
from .models import Employee


class EmployeeSerializer(serializers.ModelSerializer):
    employment_type_display = serializers.CharField(
        source='get_employment_type_display', 
        read_only=True
    )
    
    class Meta:
        model = Employee
        fields = [
            'id',
            'employee_id',
            'employee_name', 
            'phone_number',
            'employment_type',
            'employment_type_display',
            'pay',
            'is_active',
            'date_hired',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'date_hired', 'created_at', 'updated_at']
    
    def validate_employee_id(self, value):
        """Ensure employee_id is unique"""
        if self.instance:
            # If updating, exclude the current instance from uniqueness check
            if Employee.objects.filter(employee_id=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError("Employee ID already exists.")
        else:
            # If creating, check if employee_id already exists
            if Employee.objects.filter(employee_id=value).exists():
                raise serializers.ValidationError("Employee ID already exists.")
        return value
    
    def validate_pay(self, value):
        """Ensure pay is positive"""
        if value <= 0:
            raise serializers.ValidationError("Pay must be a positive number.")
        return value


class EmployeeCreateSerializer(EmployeeSerializer):
    """Serializer for creating employees with required fields"""
    
    class Meta(EmployeeSerializer.Meta):
        fields = [
            'employee_id',
            'employee_name', 
            'phone_number',
            'employment_type',
            'pay',
            'is_active'
        ]


class EmployeeListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing employees"""
    employment_type_display = serializers.CharField(
        source='get_employment_type_display', 
        read_only=True
    )
    
    class Meta:
        model = Employee
        fields = [
            'id',
            'employee_id',
            'employee_name',
            'employment_type',
            'employment_type_display',
            'is_active'
        ]
