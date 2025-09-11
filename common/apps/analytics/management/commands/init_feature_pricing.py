from django.core.management.base import BaseCommand
from common.apps.analytics.models import FeaturePricing


class Command(BaseCommand):
    help = 'Initialize feature pricing for all AI features'
    
    def handle(self, *args, **options):
        """Initialize default pricing for all AI features"""
        
        # Default pricing configuration
        default_pricing = {
            # Image Generation & Editing
            'personal_painter': {'base': 15, 'per_unit': 5, 'desc': 'AI-powered personal art generation'},
            'style_transfer': {'base': 12, 'per_unit': 3, 'desc': 'Apply artistic styles to images'},
            'dream_visualizer': {'base': 18, 'per_unit': 7, 'desc': 'Turn dreams into visual art'},
            'image_meta_gen': {'base': 5, 'per_unit': 1, 'desc': 'Generate image metadata and descriptions'},
            'replicate_style_transfer': {'base': 20, 'per_unit': 8, 'desc': 'Advanced style transfer via Replicate'},
            'replicate_iconic_art': {'base': 25, 'per_unit': 10, 'desc': 'Create iconic art via Replicate'},
            'reimagine_art': {'base': 16, 'per_unit': 6, 'desc': 'Reimagine existing artwork'},
            'runware_flux_tools': {'base': 22, 'per_unit': 9, 'desc': 'Advanced image generation with FLUX'},
            
            # Video Generation
            'image_to_video': {'base': 30, 'per_unit': 15, 'desc': 'Convert images to videos'},
            'runware_image_to_video': {'base': 35, 'per_unit': 18, 'desc': 'High-quality image to video conversion'},
            'runware_text_to_video': {'base': 40, 'per_unit': 20, 'desc': 'Generate videos from text descriptions'},
            
            # Chat & Conversation
            'painter_chat': {'base': 8, 'per_unit': 2, 'desc': 'Chat with AI art assistant'},
            'dream_visualizer_chat': {'base': 10, 'per_unit': 3, 'desc': 'Interactive dream discussion'},
            'vizzy': {'base': 12, 'per_unit': 4, 'desc': 'Voice-powered AI assistant'},
            
            # Creative Tools
            'moodboard': {'base': 14, 'per_unit': 5, 'desc': 'AI-generated mood boards'},
            'poster': {'base': 18, 'per_unit': 7, 'desc': 'Automated poster design'},
            'brand_asset': {'base': 25, 'per_unit': 10, 'desc': 'Brand asset generation'},
            'mindscape': {'base': 16, 'per_unit': 6, 'desc': 'Visual mind mapping'},
            'book_to_frames': {'base': 20, 'per_unit': 8, 'desc': 'Convert books to visual frames'},
            'visual_journal': {'base': 15, 'per_unit': 5, 'desc': 'AI-enhanced visual journaling'},
            'story_visualizer': {'base': 22, 'per_unit': 9, 'desc': 'Turn stories into visuals'},
            'text_visualization': {'base': 12, 'per_unit': 4, 'desc': 'Visualize text content'},
            'storyboard': {'base': 24, 'per_unit': 10, 'desc': 'Create professional storyboards'},
            
            # Audio
            'audio_processing': {'base': 18, 'per_unit': 6, 'desc': 'AI audio analysis and processing'},
            
            # Others
            'embedding': {'base': 5, 'per_unit': 1, 'desc': 'Generate text embeddings'},
            'onboard': {'base': 0, 'per_unit': 0, 'desc': 'Free AI onboarding assistance'},
        }
        
        created_count = 0
        updated_count = 0
        
        for feature_name, pricing in default_pricing.items():
            feature_pricing, created = FeaturePricing.objects.update_or_create(
                feature_name=feature_name,
                defaults={
                    'base_credits': pricing['base'],
                    'per_unit_credits': pricing['per_unit'],
                    'description': pricing['desc'],
                    'tier_1_limit': 5 if pricing['base'] > 0 else 0,  # 5 free uses for paid features
                    'tier_1_price': 0,  # Free tier
                    'tier_2_price': pricing['base'],  # Standard pricing
                    'tier_3_price': max(1, pricing['base'] - 5),  # Premium discount
                    'is_active': True,
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'Created pricing for {feature_name}: {pricing["base"]} credits')
            else:
                updated_count += 1
                self.stdout.write(f'Updated pricing for {feature_name}: {pricing["base"]} credits')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully initialized feature pricing. '
                f'Created: {created_count}, Updated: {updated_count}'
            )
        )
