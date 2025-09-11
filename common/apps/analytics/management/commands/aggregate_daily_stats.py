from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from common.apps.analytics.models import FeatureUsage, DailyUserStats
from collections import defaultdict


class Command(BaseCommand):
    help = 'Aggregate daily user statistics from feature usage data'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to process (default: 7)'
        )
        parser.add_argument(
            '--date',
            type=str,
            help='Specific date to process (YYYY-MM-DD format)'
        )
    
    def handle(self, *args, **options):
        if options['date']:
            # Process specific date
            try:
                from datetime import datetime
                target_date = datetime.strptime(options['date'], '%Y-%m-%d').date()
                self.process_date(target_date)
            except ValueError:
                self.stdout.write(
                    self.style.ERROR('Invalid date format. Use YYYY-MM-DD')
                )
                return
        else:
            # Process last N days
            days = options['days']
            end_date = timezone.now().date()
            
            for i in range(days):
                target_date = end_date - timedelta(days=i)
                self.process_date(target_date)
        
        self.stdout.write(
            self.style.SUCCESS('Successfully aggregated daily statistics')
        )
    
    def process_date(self, target_date):
        """Process statistics for a specific date"""
        self.stdout.write(f'Processing statistics for {target_date}...')
        
        # Get all usage records for this date
        usage_records = FeatureUsage.objects.filter(
            created_at__date=target_date
        ).select_related('user')
        
        # Group by user
        user_stats = defaultdict(lambda: {
            'total_requests': 0,
            'credits_spent': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'features': set(),
            'categories': set(),
            'feature_breakdown': defaultdict(int),
            'category_breakdown': defaultdict(int),
        })
        
        for record in usage_records:
            user_id = record.user.id
            stats = user_stats[user_id]
            
            stats['total_requests'] += 1
            stats['credits_spent'] += record.credits_used
            stats['features'].add(record.feature_name)
            stats['categories'].add(record.feature_category)
            stats['feature_breakdown'][record.feature_name] += 1
            stats['category_breakdown'][record.feature_category] += 1
            
            if record.status == 'completed':
                stats['successful_requests'] += 1
            elif record.status == 'failed':
                stats['failed_requests'] += 1
        
        # Create or update daily stats records
        for user_id, stats in user_stats.items():
            daily_stat, created = DailyUserStats.objects.update_or_create(
                user_id=user_id,
                date=target_date,
                defaults={
                    'total_ai_requests': stats['total_requests'],
                    'unique_features_used': len(stats['features']),
                    'total_credits_spent': stats['credits_spent'],
                    'successful_requests': stats['successful_requests'],
                    'failed_requests': stats['failed_requests'],
                    'feature_usage_breakdown': dict(stats['feature_breakdown']),
                    'category_usage_breakdown': dict(stats['category_breakdown']),
                }
            )
            
            action = "Created" if created else "Updated"
            self.stdout.write(f'  {action} stats for user {user_id}')
        
        self.stdout.write(f'Processed {len(user_stats)} users for {target_date}')
