from django.db import migrations, models
import common.apps.utils.user_directory._user_directory_path

class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0012_merge_20250718_0656'),
    ]

    operations = [
        migrations.AddField(
            model_name='audio',
            name='music_cover',
            field=models.ImageField(upload_to=common.apps.utils.user_directory._user_directory_path.user_image_path, blank=True, null=True, max_length=500, help_text="Optional cover photo for the audio"),
        ),
    ] 