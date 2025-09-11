from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import FeatureUsage, UserSession, DailyUserStats, FeaturePricing
from common.apps.credits.services import CreditService
from common.apps.credits.models import CreditAIOperation
import logging
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple

User = get_user_model()
logger = logging.getLogger(__name__)


class FeatureUsageTracker:
    """Service for tracking AI feature usage and billing"""
    
    @staticmethod
    def get_feature_category(feature_name: str) -> str:
        """Map feature name to category"""
        category_mapping = {
            # Image Generation & Editing
            'personal_painter': 'image_generation',
            'style_transfer': 'style_transfer',
            'dream_visualizer': 'image_generation',
            'image_meta_gen': 'image_editing',
            'replicate_style_transfer': 'style_transfer',
            'replicate_iconic_art': 'image_generation',
            'reimagine_art': 'image_editing',
            'runware_flux_tools': 'image_generation',
            
            # Video
            'image_to_video': 'video_generation',
            'runware_image_to_video': 'video_generation',
            'runware_text_to_video': 'video_generation',
            
            # Chat & Conversation
            'painter_chat': 'chat_ai',
            'dream_visualizer_chat': 'chat_ai',
            'vizzy': 'chat_ai',
            
            # Creative Tools
            'moodboard': 'creative_tools',
            'poster': 'creative_tools',
            'brand_asset': 'creative_tools',
            'mindscape': 'creative_tools',
            'book_to_frames': 'creative_tools',
            'visual_journal': 'creative_tools',
            'story_visualizer': 'creative_tools',
            'text_visualization': 'visualization',
            
            # Audio
            'audio_processing': 'audio_processing',
            
            # Others
            'embedding': 'text_processing',
            'onboard': 'chat_ai',
            'storyboard': 'creative_tools',
        }
        return category_mapping.get(feature_name, 'creative_tools')
    
    @staticmethod
    @transaction.atomic
    def start_feature_usage(
        user: User,
        feature_name: str,
        input_data: Dict[str, Any] = None,
        session_id: str = None,
        endpoint_path: str = "",
        user_agent: str = "",
        ip_address: str = None
    ) -> Tuple[FeatureUsage, bool, str]:
        """
        Start tracking feature usage and deduct credits if needed
        Returns: (usage_record, success, message)
        """
        try:
            # Get feature pricing
            feature_category = FeatureUsageTracker.get_feature_category(feature_name)
            
            try:
                pricing = FeaturePricing.objects.get(feature_name=feature_name, is_active=True)
                credits_needed = pricing.base_credits
            except FeaturePricing.DoesNotExist:
                # Fallback to credit pricing from existing system
                credits_needed = CreditService.get_operation_cost(feature_category, 1)
            
            # Check and deduct credits
            credit_success, credit_operation_id, credit_message = CreditService.use_credits(
                user=user,
                amount=credits_needed,
                operation_type=feature_category,
                input_data=input_data,
                ai_operation_id=None
            )
            
            if not credit_success:
                # Create failed usage record
                usage_record = FeatureUsage.objects.create(
                    user=user,
                    feature_name=feature_name,
                    feature_category=feature_category,
                    session_id=session_id,
                    status='failed',
                    credits_used=0,
                    input_data=input_data,
                    endpoint_path=endpoint_path,
                    user_agent=user_agent[:500] if user_agent else "",
                    ip_address=ip_address,
                    error_message=credit_message,
                    error_code='INSUFFICIENT_CREDITS'
                )
                return usage_record, False, credit_message
            
            # Get credit operation for linking
            credit_operation = None
            if credit_operation_id:
                try:
                    credit_operation = CreditAIOperation.objects.get(id=credit_operation_id)
                except CreditAIOperation.DoesNotExist:
                    pass
            
            # Create successful usage record
            usage_record = FeatureUsage.objects.create(
                user=user,
                feature_name=feature_name,
                feature_category=feature_category,
                session_id=session_id,
                status='in_progress',
                credits_used=credits_needed,
                input_data=input_data,
                endpoint_path=endpoint_path,
                user_agent=user_agent[:500] if user_agent else "",
                ip_address=ip_address,
                credit_operation=credit_operation
            )
            
            # Update user session stats
            FeatureUsageTracker._update_session_stats(user, session_id, credits_needed)
            
            logger.info(
                f"Started feature usage tracking: user={user.username}, "
                f"feature={feature_name}, credits={credits_needed}, usage_id={usage_record.id}"
            )
            
            return usage_record, True, "Feature usage started successfully"
            
        except Exception as e:
            logger.error(f"Error starting feature usage tracking: {str(e)}")
            # Create error record
            usage_record = FeatureUsage.objects.create(
                user=user,
                feature_name=feature_name,
                feature_category=FeatureUsageTracker.get_feature_category(feature_name),
                session_id=session_id,
                status='failed',
                credits_used=0,
                input_data=input_data,
                endpoint_path=endpoint_path,
                user_agent=user_agent[:500] if user_agent else "",
                ip_address=ip_address,
                error_message=str(e),
                error_code='SYSTEM_ERROR'
            )
            return usage_record, False, f"System error: {str(e)}"
    
    @staticmethod
    @transaction.atomic
    def complete_feature_usage(
        usage_record: FeatureUsage,
        output_data: Dict[str, Any] = None,
        response_body: Dict[str, Any] = None,
        processing_time: float = None,
        status: str = 'completed'
    ) -> bool:
        """Complete feature usage tracking"""
        try:
            usage_record.status = status
            
            # Store metadata in output_data
            if output_data is None:
                output_data = {}
            
            # Store the actual API response separately in output_data under response_body
            if response_body is not None:
                output_data['response_body'] = response_body
            
            usage_record.output_data = output_data
            usage_record.processing_time = processing_time
            usage_record.save()
            
            # Update credit operation status
            if usage_record.credit_operation:
                usage_record.credit_operation.status = 'completed' if status == 'completed' else 'failed'
                usage_record.credit_operation.result_data = output_data
                usage_record.credit_operation.save()
            
            # Update daily stats
            FeatureUsageTracker._update_daily_stats(usage_record)
            
            logger.info(f"Completed feature usage: usage_id={usage_record.id}, status={status}")
            return True
            
        except Exception as e:
            logger.error(f"Error completing feature usage: {str(e)}")
            return False
    
    @staticmethod
    def fail_feature_usage(
        usage_record: FeatureUsage,
        error_message: str,
        error_code: str = 'PROCESSING_FAILED',
        refund_credits: bool = True
    ) -> bool:
        """Mark feature usage as failed and optionally refund credits"""
        try:
            usage_record.status = 'failed'
            usage_record.error_message = error_message
            usage_record.error_code = error_code
            usage_record.save()
            
            # Refund credits if requested
            if refund_credits and usage_record.credit_operation:
                success, message = CreditService.refund_credits(usage_record.credit_operation.id)
                if success:
                    logger.info(f"Refunded credits for failed usage: usage_id={usage_record.id}")
                else:
                    logger.warning(f"Failed to refund credits: {message}")
            
            # Update daily stats
            FeatureUsageTracker._update_daily_stats(usage_record)
            
            logger.info(f"Failed feature usage: usage_id={usage_record.id}, error={error_message}")
            return True
            
        except Exception as e:
            logger.error(f"Error failing feature usage: {str(e)}")
            return False
    
    @staticmethod
    def _update_session_stats(user: User, session_id: str, credits_spent: int):
        """Update user session statistics"""
        if not session_id:
            return
        
        try:
            session = UserSession.objects.get(session_id=session_id, user=user, is_active=True)
            session.total_ai_features_used += 1
            session.total_credits_spent += credits_spent
            session.total_requests += 1
            session.last_activity = timezone.now()
            session.save()
        except UserSession.DoesNotExist:
            logger.warning(f"Session not found for user {user.username}: {session_id}")
    
    @staticmethod
    def _update_daily_stats(usage_record: FeatureUsage):
        """Update daily user statistics"""
        try:
            today = timezone.now().date()
            stats, created = DailyUserStats.objects.get_or_create(
                user=usage_record.user,
                date=today,
                defaults={
                    'feature_usage_breakdown': {},
                    'category_usage_breakdown': {}
                }
            )
            
            # Update counters
            stats.total_ai_requests += 1
            stats.total_credits_spent += usage_record.credits_used
            
            if usage_record.status == 'completed':
                stats.successful_requests += 1
            elif usage_record.status == 'failed':
                stats.failed_requests += 1
            
            # Update feature breakdown
            feature_breakdown = stats.feature_usage_breakdown or {}
            feature_breakdown[usage_record.feature_name] = feature_breakdown.get(usage_record.feature_name, 0) + 1
            stats.feature_usage_breakdown = feature_breakdown
            
            # Update category breakdown
            category_breakdown = stats.category_usage_breakdown or {}
            category_breakdown[usage_record.feature_category] = category_breakdown.get(usage_record.feature_category, 0) + 1
            stats.category_usage_breakdown = category_breakdown
            
            # Calculate unique features used
            stats.unique_features_used = len(feature_breakdown.keys())
            
            stats.save()
            
        except Exception as e:
            logger.error(f"Error updating daily stats: {str(e)}")
    
    @staticmethod
    def get_user_usage_summary(user: User, days: int = 30) -> Dict[str, Any]:
        """Get user usage summary for the last N days"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Get feature usage records
        usage_records = FeatureUsage.objects.filter(
            user=user,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).values('feature_name', 'status', 'credits_used').order_by('created_at')
        
        # Get daily stats
        daily_stats = DailyUserStats.objects.filter(
            user=user,
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')
        
        # Calculate summary
        total_requests = len(usage_records)
        total_credits = sum(record['credits_used'] for record in usage_records)
        successful_requests = len([r for r in usage_records if r['status'] == 'completed'])
        failed_requests = len([r for r in usage_records if r['status'] == 'failed'])
        
        # Feature usage breakdown
        feature_counts = {}
        for record in usage_records:
            feature_counts[record['feature_name']] = feature_counts.get(record['feature_name'], 0) + 1
        
        return {
            'period_days': days,
            'total_requests': total_requests,
            'total_credits_spent': total_credits,
            'successful_requests': successful_requests,
            'failed_requests': failed_requests,
            'success_rate': round(successful_requests / total_requests * 100, 2) if total_requests > 0 else 0,
            'unique_features_used': len(feature_counts.keys()),
            'feature_usage_breakdown': feature_counts,
            'daily_stats': [
                {
                    'date': stat.date.isoformat(),
                    'requests': stat.total_ai_requests,
                    'credits': stat.total_credits_spent,
                    'success_rate': round(stat.successful_requests / max(stat.total_ai_requests, 1) * 100, 2)
                }
                for stat in daily_stats
            ]
        }
    
    @staticmethod
    def create_user_session(
        user: User,
        platform: str = 'web',
        ip_address: str = None,
        user_agent: str = "",
        device_info: Dict[str, Any] = None
    ) -> UserSession:
        """Create a new user session"""
        session_id = str(uuid.uuid4())
        
        session = UserSession.objects.create(
            user=user,
            session_id=session_id,
            platform=platform,
            ip_address=ip_address,
            user_agent=user_agent[:500] if user_agent else "",
            device_info=device_info or {}
        )
        
        logger.info(f"Created user session: {session_id} for user {user.username}")
        return session
    
    @staticmethod
    def end_user_session(session_id: str) -> bool:
        """End a user session"""
        try:
            session = UserSession.objects.get(session_id=session_id, is_active=True)
            session.is_active = False
            session.end_time = timezone.now()
            session.save()
            logger.info(f"Ended user session: {session_id}")
            return True
        except UserSession.DoesNotExist:
            logger.warning(f"Session not found or already ended: {session_id}")
            return False


class AnalyticsService:
    """Service for analytics and reporting"""
    
    @staticmethod
    def get_platform_usage_stats(days: int = 30) -> Dict[str, Any]:
        """Get platform-wide usage statistics"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Get all usage records in the period
        usage_records = FeatureUsage.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).select_related('user')
        
        # Calculate statistics
        total_users = usage_records.values('user').distinct().count()
        total_requests = usage_records.count()
        total_credits = sum(record.credits_used for record in usage_records)
        
        # Feature popularity
        feature_counts = {}
        category_counts = {}
        
        for record in usage_records:
            feature_counts[record.feature_name] = feature_counts.get(record.feature_name, 0) + 1
            category_counts[record.feature_category] = category_counts.get(record.feature_category, 0) + 1
        
        # Sort by popularity
        popular_features = sorted(feature_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        popular_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'period_days': days,
            'total_active_users': total_users,
            'total_requests': total_requests,
            'total_credits_spent': total_credits,
            'average_requests_per_user': round(total_requests / max(total_users, 1), 2),
            'average_credits_per_user': round(total_credits / max(total_users, 1), 2),
            'popular_features': popular_features,
            'category_usage': popular_categories
        }
