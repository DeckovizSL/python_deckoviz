from django.core.management.base import BaseCommand
from common.apps.modes.models import Mode

class Command(BaseCommand):
    help = 'Creates the default modes in the database'

    def handle(self, *args, **options):
        modes = ['serenity', 'romantic', 'inspiration', 'focus', 'meditation']
        for mode_name in modes:
            mode, created = Mode.objects.get_or_create(name=mode_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Successfully created mode: {mode_name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Mode already exists: {mode_name}')) 