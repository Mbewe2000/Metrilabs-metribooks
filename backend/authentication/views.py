from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth import authenticate, logout
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from django_ratelimit.core import is_ratelimited
import random
import string
import logging

# Get loggers
auth_logger = logging.getLogger('authentication')
security_logger = logging.getLogger('security')
rate_limit_logger = logging.getLogger('rate_limit')

from .models import CustomUser
from .serializers import (
    UserRegistrationSerializer, 
    LoginSerializer, 
    ChangePasswordSerializer,
    ResetPasswordSerializer,
    UserProfileSerializer
)


class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        client_ip = self.get_client_ip(request)
        
        # Check rate limit
        ratelimited = is_ratelimited(
            request=request,
            group='register',
            key='ip',
            rate='5/m',
            method=['POST'],
            increment=True
        )
        
        if ratelimited:
            rate_limit_logger.warning(
                f"Registration rate limit exceeded from IP: {client_ip}"
            )
            return Response({
                'error': 'Rate limit exceeded. Please try again later.',
                'detail': 'Maximum 5 registration attempts per minute allowed.',
                'retry_after': '60 seconds'
            }, status=429)
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            
            # Log successful registration
            auth_logger.info(
                f"New user registered: {user.email or user.phone} from IP: {client_ip}"
            )
            
            return Response({
                'message': 'User registered successfully',
                'user': UserProfileSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_201_CREATED)
        
        # Log failed registration attempt
        auth_logger.warning(
            f"Failed registration attempt from IP: {client_ip}, errors: {serializer.errors}"
        )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        client_ip = self.get_client_ip(request)
        email_or_phone = request.data.get('email_or_phone', 'unknown')
        
        # Check rate limit
        ratelimited = is_ratelimited(
            request=request,
            group='login',
            key='ip',
            rate='10/m',
            method=['POST'],
            increment=True
        )
        
        if ratelimited:
            rate_limit_logger.warning(
                f"Login rate limit exceeded from IP: {client_ip}, attempted user: {email_or_phone}"
            )
            return Response({
                'error': 'Rate limit exceeded. Please try again later.',
                'detail': 'Maximum 10 login attempts per minute allowed.',
                'retry_after': '60 seconds'
            }, status=429)
        
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            
            # Log successful login
            auth_logger.info(
                f"Successful login: {user.email or user.phone} from IP: {client_ip}"
            )
            
            return Response({
                'message': 'Login successful',
                'user': UserProfileSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_200_OK)
        
        # Log failed login attempt
        security_logger.warning(
            f"Failed login attempt for: {email_or_phone} from IP: {client_ip}, errors: {serializer.errors}"
        )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        client_ip = self.get_client_ip(request)
        user = request.user
        
        try:
            refresh_token = request.data.get("refresh_token")
            if not refresh_token:
                return Response({
                    'error': 'Refresh token is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            # Log successful logout
            auth_logger.info(
                f"User logged out: {user.email or user.phone} from IP: {client_ip}"
            )
            
            return Response({
                'message': 'Logout successful'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            # Log logout failure
            auth_logger.error(
                f"Logout failed for user: {user.email or user.phone} from IP: {client_ip}, error: {str(e)}"
            )
            return Response({
                'error': f'Logout failed: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        client_ip = self.get_client_ip(request)
        user = request.user
        
        # Check rate limit
        ratelimited = is_ratelimited(
            request=request,
            group='change_password',
            key='user',
            rate='5/m',
            method=['PUT'],
            increment=True
        )
        
        if ratelimited:
            rate_limit_logger.warning(
                f"Password change rate limit exceeded for user: {user.email or user.phone} from IP: {client_ip}"
            )
            return Response({
                'error': 'Rate limit exceeded. Please try again later.',
                'detail': 'Maximum 5 password change attempts per minute allowed.',
                'retry_after': '60 seconds'
            }, status=429)
        
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            # Log successful password change
            security_logger.info(
                f"Password changed successfully for user: {user.email or user.phone} from IP: {client_ip}"
            )
            
            return Response({
                'message': 'Password changed successfully'
            }, status=status.HTTP_200_OK)
        
        # Log failed password change attempt
        security_logger.warning(
            f"Failed password change attempt for user: {user.email or user.phone} from IP: {client_ip}, errors: {serializer.errors}"
        )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        client_ip = self.get_client_ip(request)
        
        # Check rate limit
        ratelimited = is_ratelimited(
            request=request,
            group='reset_password',
            key='ip',
            rate='3/m',
            method=['POST'],
            increment=True
        )
        
        if ratelimited:
            rate_limit_logger.warning(
                f"Password reset rate limit exceeded from IP: {client_ip}"
            )
            return Response({
                'error': 'Rate limit exceeded. Please try again later.',
                'detail': 'Maximum 3 password reset attempts per minute allowed.',
                'retry_after': '60 seconds'
            }, status=429)
        
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email_or_phone = serializer.validated_data['email_or_phone']
            
            # Find user
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
            
            if user:
                # Log password reset request
                security_logger.info(
                    f"Password reset requested for user: {user.email or user.phone} from IP: {client_ip}"
                )
                
                # Generate reset token
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                
                # For email reset
                if '@' in email_or_phone:
                    return Response({
                        'message': 'Password reset link sent to your email',
                        'reset_token': token,  # Remove this in production
                        'uid': uid  # Remove this in production
                    }, status=status.HTTP_200_OK)
                else:
                    # For phone reset
                    reset_code = ''.join(random.choices(string.digits, k=6))
                    return Response({
                        'message': 'Password reset code sent to your phone',
                        'reset_code': reset_code  # Remove this in production
                    }, status=status.HTTP_200_OK)
            else:
                # Log failed reset attempt
                security_logger.warning(
                    f"Password reset attempted for non-existent user: {email_or_phone} from IP: {client_ip}"
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class ResetPasswordConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        # Check rate limit
        ratelimited = is_ratelimited(
            request=request,
            group='reset_password_confirm',
            key='ip',
            rate='10/m',
            method=['POST'],
            increment=True
        )
        
        if ratelimited:
            return Response({
                'error': 'Rate limit exceeded. Please try again later.',
                'detail': 'Maximum 10 password reset confirmation attempts per minute allowed.',
                'retry_after': '60 seconds'
            }, status=429)
        
        uid = request.data.get('uid')
        token = request.data.get('token')
        new_password = request.data.get('new_password')
        if not all([uid, token, new_password]):
            return Response({
                'error': 'UID, token, and new password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = CustomUser.objects.get(pk=user_id)
            
            if default_token_generator.check_token(user, token):
                user.set_password(new_password)
                user.save()
                return Response({
                    'message': 'Password reset successful'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Invalid token'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            return Response({
                'error': 'Invalid user'
            }, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
