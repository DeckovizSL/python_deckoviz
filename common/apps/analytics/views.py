from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from .models import FeatureUsage, UserSession, DailyUserStats, FeaturePricing
from .services import FeatureUsageTracker, AnalyticsService
from .serializers import (
    FeatureUsageSerializer, 
    UserSessionSerializer, 
    DailyUserStatsSerializer,
    FeaturePricingSerializer,
    UsageTrackingStartSerializer,
    UsageTrackingCompleteSerializer,
    UsageTrackingFailSerializer
)
import json
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([])  # No auth required for internal API calls
def start_usage_tracking(request):
    """API endpoint to start usage tracking (called from FastAPI)"""
    try:
        serializer = UsageTrackingStartSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Invalid request data',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        # Get user
        try:
            user = User.objects.get(id=data['user_id'])
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Start usage tracking
        usage_record, success, message = FeatureUsageTracker.start_feature_usage(
            user=user,
            feature_name=data['feature_name'],
            input_data=data.get('input_data'),
            session_id=data.get('session_id'),
            endpoint_path=data.get('endpoint_path', ''),
            user_agent=data.get('user_agent', ''),
            ip_address=data.get('ip_address')
        )
        
        return Response({
            'success': success,
            'message': message,
            'usage_id': str(usage_record.id) if usage_record else None,
            'credits_used': usage_record.credits_used if usage_record else 0
        })
        
    except Exception as e:
        logger.error(f"Error in start_usage_tracking: {str(e)}")
        return Response({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([])  # No auth required for internal API calls
def complete_usage_tracking(request):
    """API endpoint to complete usage tracking (called from FastAPI)"""
    try:
        serializer = UsageTrackingCompleteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Invalid request data',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        # Get usage record
        try:
            usage_record = FeatureUsage.objects.get(id=data['usage_id'])
        except FeatureUsage.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Usage record not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Complete usage tracking
        success = FeatureUsageTracker.complete_feature_usage(
            usage_record=usage_record,
            output_data=data.get('output_data'),
            response_body=data.get('response_body'),
            processing_time=data.get('processing_time'),
            status=data.get('status', 'completed')
        )
        
        return Response({
            'success': success,
            'message': 'Usage tracking completed' if success else 'Failed to complete usage tracking'
        })
        
    except Exception as e:
        logger.error(f"Error in complete_usage_tracking: {str(e)}")
        return Response({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([])  # No auth required for internal API calls
def fail_usage_tracking(request):
    """API endpoint to mark usage as failed (called from FastAPI)"""
    try:
        serializer = UsageTrackingFailSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Invalid request data',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        # Get usage record
        try:
            usage_record = FeatureUsage.objects.get(id=data['usage_id'])
        except FeatureUsage.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Usage record not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Fail usage tracking
        success = FeatureUsageTracker.fail_feature_usage(
            usage_record=usage_record,
            error_message=data['error_message'],
            error_code=data.get('error_code', 'API_ERROR'),
            refund_credits=data.get('refund_credits', True)
        )
        
        return Response({
            'success': success,
            'message': 'Usage tracking failed' if success else 'Failed to mark usage as failed'
        })
        
    except Exception as e:
        logger.error(f"Error in fail_usage_tracking: {str(e)}")
        return Response({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserFeatureUsageListView(generics.ListAPIView):
    """Get user's feature usage history"""
    serializer_class = FeatureUsageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        days = int(self.request.query_params.get('days', 30))
        
        from django.utils import timezone
        from datetime import timedelta
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        return FeatureUsage.objects.filter(
            user=user,
            created_at__gte=start_date
        ).order_by('-created_at')


class UserUsageSummaryView(generics.GenericAPIView):
    """Get user's usage summary and statistics"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        days = int(request.query_params.get('days', 30))
        
        summary = FeatureUsageTracker.get_user_usage_summary(user, days)
        
        return Response({
            'success': True,
            'data': summary
        })


class UserSessionListView(generics.ListAPIView):
    """Get user's session history"""
    serializer_class = UserSessionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        limit = int(self.request.query_params.get('limit', 50))
        
        return UserSession.objects.filter(user=user).order_by('-start_time')[:limit]


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_user_session(request):
    """Create a new user session"""
    try:
        platform = request.data.get('platform', 'web')
        device_info = request.data.get('device_info', {})
        
        # Get IP and user agent from request
        ip_address = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
        if not ip_address:
            ip_address = request.META.get('REMOTE_ADDR')
        
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        session = FeatureUsageTracker.create_user_session(
            user=request.user,
            platform=platform,
            ip_address=ip_address,
            user_agent=user_agent,
            device_info=device_info
        )
        
        serializer = UserSessionSerializer(session)
        return Response({
            'success': True,
            'session': serializer.data
        })
        
    except Exception as e:
        logger.error(f"Error creating user session: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error creating session: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def end_user_session(request, session_id):
    """End a user session"""
    try:
        success = FeatureUsageTracker.end_user_session(session_id)
        
        return Response({
            'success': success,
            'message': 'Session ended successfully' if success else 'Session not found or already ended'
        })
        
    except Exception as e:
        logger.error(f"Error ending user session: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error ending session: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DailyStatsListView(generics.ListAPIView):
    """Get user's daily statistics"""
    serializer_class = DailyUserStatsSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        days = int(self.request.query_params.get('days', 30))
        
        from django.utils import timezone
        from datetime import timedelta
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        return DailyUserStats.objects.filter(
            user=user,
            date__gte=start_date
        ).order_by('-date')


class FeaturePricingListView(generics.ListAPIView):
    """Get current feature pricing"""
    serializer_class = FeaturePricingSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return FeaturePricing.objects.filter(is_active=True).order_by('feature_name')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_feature_cost(request, feature_name):
    """Get the cost for a specific feature"""
    try:
        pricing = FeaturePricing.objects.get(feature_name=feature_name, is_active=True)
        user_tier = 1  # You can implement user tier logic here
        
        cost = pricing.calculate_cost(usage_count=1, user_tier=user_tier)
        
        return Response({
            'feature_name': feature_name,
            'base_credits': pricing.base_credits,
            'calculated_cost': cost,
            'user_tier': user_tier,
            'description': pricing.description
        })
        
    except FeaturePricing.DoesNotExist:
        # Fallback to default pricing
        from common.apps.credits.services import CreditService
        category = FeatureUsageTracker.get_feature_category(feature_name)
        cost = CreditService.get_operation_cost(category, 1)
        
        return Response({
            'feature_name': feature_name,
            'base_credits': cost,
            'calculated_cost': cost,
            'user_tier': 1,
            'description': f'Default pricing for {category}'
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def platform_analytics(request):
    """Get platform-wide analytics (admin only)"""
    if not request.user.is_staff:
        return Response({
            'error': 'Permission denied'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        days = int(request.query_params.get('days', 30))
        stats = AnalyticsService.get_platform_usage_stats(days)
        
        return Response({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting platform analytics: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error getting analytics: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
