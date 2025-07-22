from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
import logging

from .models import UserProfile
from .serializers import (
    UserProfileSerializer,
    UserProfileCreateUpdateSerializer,
    UserProfileSummarySerializer
)

# Get logger
logger = logging.getLogger('profiles')

User = get_user_model()


class UserProfileView(generics.RetrieveAPIView):
    """
    Get user profile information
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        if created:
            logger.info(f"New profile created for user: {self.request.user.email}")
        return profile

    def get(self, request, *args, **kwargs):
        try:
            profile = self.get_object()
            serializer = self.get_serializer(profile)
            
            logger.info(f"Profile retrieved for user: {request.user.email}")
            return Response({
                'success': True,
                'message': 'Profile retrieved successfully',
                'data': serializer.data
            })
        except Exception as e:
            logger.error(f"Error retrieving profile for user {request.user.email}: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error retrieving profile',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserProfileUpdateView(generics.RetrieveUpdateAPIView):
    """
    Update user profile information
    """
    serializer_class = UserProfileCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile

    def update(self, request, *args, **kwargs):
        # Rate limiting check
        from django_ratelimit.core import is_ratelimited
        if is_ratelimited(request, group='profile_update', key='ip', rate='10/m', method='ALL'):
            logger.warning(f"Rate limit exceeded for profile update by IP: {request.META.get('REMOTE_ADDR')}")
            return Response({
                'success': False,
                'message': 'Rate limit exceeded. Please try again later.',
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        if serializer.is_valid():
            try:
                serializer.save()
                logger.info(f"Profile updated for user: {request.user.email}")
                
                # Return full profile data
                full_serializer = UserProfileSerializer(instance)
                return Response({
                    'success': True,
                    'message': 'Profile updated successfully',
                    'data': full_serializer.data
                })
            except Exception as e:
                logger.error(f"Error updating profile for user {request.user.email}: {str(e)}")
                return Response({
                    'success': False,
                    'message': 'Error updating profile',
                    'error': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            logger.warning(f"Invalid profile update data for user {request.user.email}: {serializer.errors}")
            return Response({
                'success': False,
                'message': 'Invalid data provided',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
@ratelimit(key='ip', rate='20/m', method='GET')
def profile_summary(request):
    """
    Get a summary of the user's profile
    """
    try:
        profile = get_object_or_404(UserProfile, user=request.user)
        serializer = UserProfileSummarySerializer(profile)
        
        logger.info(f"Profile summary retrieved for user: {request.user.email}")
        return Response({
            'success': True,
            'message': 'Profile summary retrieved successfully',
            'data': serializer.data
        })
    except UserProfile.DoesNotExist:
        logger.info(f"No profile found for user: {request.user.email}")
        return Response({
            'success': False,
            'message': 'Profile not found. Please create your profile first.',
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error retrieving profile summary for user {request.user.email}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Error retrieving profile summary',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
@ratelimit(key='ip', rate='10/m', method='GET')
def profile_completion_status(request):
    """
    Check profile completion status
    """
    try:
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        completion_data = {
            'is_complete': profile.is_complete,
            'completion_percentage': profile.get_completion_percentage(),
            'missing_fields': []
        }
        
        # Check which required fields are missing
        if not profile.first_name:
            completion_data['missing_fields'].append('first_name')
        if not profile.last_name:
            completion_data['missing_fields'].append('last_name')
        if not profile.business_name:
            completion_data['missing_fields'].append('business_name')
        if not profile.business_type:
            completion_data['missing_fields'].append('business_type')
        if not profile.business_subcategory:
            completion_data['missing_fields'].append('business_subcategory')
        if not profile.business_city:
            completion_data['missing_fields'].append('business_city')
        if not profile.business_province:
            completion_data['missing_fields'].append('business_province')
        
        logger.info(f"Profile completion status checked for user: {request.user.email}")
        return Response({
            'success': True,
            'message': 'Profile completion status retrieved successfully',
            'data': completion_data
        })
    except Exception as e:
        logger.error(f"Error checking profile completion for user {request.user.email}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Error checking profile completion status',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
@ratelimit(key='ip', rate='30/m', method='GET')
def business_subcategories(request):
    """
    Get subcategory choices for a specific business type
    """
    try:
        business_type = request.GET.get('business_type')
        if not business_type:
            return Response({
                'success': False,
                'message': 'business_type parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create a temporary profile instance to get subcategories
        temp_profile = UserProfile(business_type=business_type)
        subcategories = temp_profile.get_subcategory_choices()
        
        # Get all business types for reference
        business_types = UserProfile.BUSINESS_TYPE_CHOICES
        
        return Response({
            'success': True,
            'message': 'Subcategories retrieved successfully',
            'data': {
                'business_type': business_type,
                'subcategories': subcategories,
                'business_types': business_types
            }
        })
    except Exception as e:
        logger.error(f"Error retrieving subcategories for business type {business_type}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Error retrieving subcategories',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
