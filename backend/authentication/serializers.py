from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import CustomUser


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ('email', 'phone', 'password', 'password_confirm')

    def validate(self, attrs):
        if not attrs.get('email') and not attrs.get('phone'):
            raise serializers.ValidationError("Either email or phone must be provided")
        
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords do not match")
        
        # Check if email already exists
        if attrs.get('email') and CustomUser.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError("Email already exists")
        
        # Check if phone already exists
        if attrs.get('phone') and CustomUser.objects.filter(phone=attrs['phone']).exists():
            raise serializers.ValidationError("Phone number already exists")
        
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = CustomUser.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    email_or_phone = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        email_or_phone = attrs.get('email_or_phone')
        password = attrs.get('password')

        if email_or_phone and password:
            # Try to find user by email first, then by phone
            user = None
            if '@' in email_or_phone:
                try:
                    user = CustomUser.objects.get(email=email_or_phone)
                except CustomUser.DoesNotExist:
                    pass
            else:
                try:
                    user = CustomUser.objects.get(phone=email_or_phone)
                except CustomUser.DoesNotExist:
                    pass

            if user and user.check_password(password):
                if not user.is_active:
                    raise serializers.ValidationError('User account is disabled.')
                attrs['user'] = user
                return attrs
            else:
                raise serializers.ValidationError('Invalid credentials.')
        else:
            raise serializers.ValidationError('Must include email/phone and password.')

        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New passwords do not match")
        return attrs

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect")
        return value


class ResetPasswordSerializer(serializers.Serializer):
    email_or_phone = serializers.CharField()

    def validate_email_or_phone(self, value):
        # Check if user exists
        user = None
        if '@' in value:
            try:
                user = CustomUser.objects.get(email=value)
            except CustomUser.DoesNotExist:
                raise serializers.ValidationError("No user found with this email.")
        else:
            try:
                user = CustomUser.objects.get(phone=value)
            except CustomUser.DoesNotExist:
                raise serializers.ValidationError("No user found with this phone number.")
        
        return value


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'phone', 'date_joined', 
                 'email_verified', 'phone_verified')
        read_only_fields = ('id', 'date_joined', 'email_verified', 'phone_verified')


class UpdateEmailSerializer(serializers.Serializer):
    new_email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True)

    def validate_new_email(self, value):
        user = self.context['request'].user
        
        # Check if email is different from current
        if user.email == value:
            raise serializers.ValidationError("New email must be different from current email.")
        
        # Check if email already exists
        if CustomUser.objects.filter(email=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("This email is already in use.")
        
        return value

    def validate_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Password is incorrect.")
        return value


class UpdatePhoneSerializer(serializers.Serializer):
    new_phone = serializers.CharField(required=True, max_length=20)
    password = serializers.CharField(required=True)

    def validate_new_phone(self, value):
        user = self.context['request'].user
        
        # Check if phone is different from current
        if user.phone == value:
            raise serializers.ValidationError("New phone number must be different from current phone number.")
        
        # Check if phone already exists
        if CustomUser.objects.filter(phone=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("This phone number is already in use.")
        
        return value

    def validate_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Password is incorrect.")
        return value
