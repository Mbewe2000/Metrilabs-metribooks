from rest_framework import serializers
from .models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    # Read-only fields from the related user
    email = serializers.EmailField(source='user.email', read_only=True)
    phone = serializers.CharField(source='user.phone', read_only=True)
    business_location = serializers.CharField(read_only=True)
    completion_percentage = serializers.SerializerMethodField()
    subcategory_choices = serializers.SerializerMethodField()
    subcategory_display = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            'id',
            'user',
            'first_name',
            'last_name',
            'full_name',
            'business_name',
            'email',
            'phone',
            'business_type',
            'business_subcategory',
            'subcategory_choices',
            'subcategory_display',
            'business_city',
            'business_province',
            'business_location',
            'employee_count',
            'monthly_revenue_range',
            'is_complete',
            'completion_percentage',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['user', 'full_name', 'is_complete', 'created_at', 'updated_at']

    def get_completion_percentage(self, obj):
        return obj.get_completion_percentage()
    
    def get_subcategory_choices(self, obj):
        return obj.get_subcategory_choices()
    
    def get_subcategory_display(self, obj):
        return obj.get_subcategory_display()

    def validate(self, data):
        """
        Custom validation for profile data
        """
        # Ensure business name is not empty if provided
        if 'business_name' in data and not data['business_name'].strip():
            raise serializers.ValidationError({
                'business_name': 'Business name cannot be empty.'
            })
        
        # Ensure first name is not empty if provided
        if 'first_name' in data and not data['first_name'].strip():
            raise serializers.ValidationError({
                'first_name': 'First name cannot be empty.'
            })
        
        # Ensure last name is not empty if provided
        if 'last_name' in data and not data['last_name'].strip():
            raise serializers.ValidationError({
                'last_name': 'Last name cannot be empty.'
            })
        
        return data


class UserProfileCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating user profiles
    """
    completion_percentage = serializers.SerializerMethodField(read_only=True)
    subcategory_choices = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'first_name',
            'last_name',
            'full_name',
            'business_name',
            'business_type',
            'business_subcategory',
            'subcategory_choices',
            'business_city',
            'business_province',
            'employee_count',
            'monthly_revenue_range',
            'completion_percentage',
        ]
        read_only_fields = ['full_name']

    def get_completion_percentage(self, obj):
        return obj.get_completion_percentage()
    
    def get_subcategory_choices(self, obj):
        return obj.get_subcategory_choices()

    def validate_first_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("First name cannot be empty.")
        return value.strip()

    def validate_last_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Last name cannot be empty.")
        return value.strip()

    def validate_business_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Business name cannot be empty.")
        return value.strip()

    def validate_business_city(self, value):
        if not value.strip():
            raise serializers.ValidationError("Business city cannot be empty.")
        return value.strip()

    def validate_business_province(self, value):
        if not value.strip():
            raise serializers.ValidationError("Business province cannot be empty.")
        return value.strip()
    
    def validate_business_subcategory(self, value):
        """Validate that subcategory matches the business type"""
        if value and hasattr(self, 'instance') and self.instance:
            valid_choices = [choice[0] for choice in self.instance.get_subcategory_choices()]
            if value not in valid_choices:
                raise serializers.ValidationError(
                    f"Invalid subcategory for the selected business type."
                )
        return value


class UserProfileSummarySerializer(serializers.ModelSerializer):
    """
    Simplified serializer for profile summaries
    """
    email = serializers.EmailField(source='user.email', read_only=True)
    phone = serializers.CharField(source='user.phone', read_only=True)
    business_location = serializers.CharField(read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'id',
            'first_name',
            'last_name',
            'full_name',
            'business_name',
            'email',
            'phone',
            'business_type',
            'business_subcategory',
            'business_location',
            'is_complete',
        ]
