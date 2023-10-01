# Generated by Django 4.1.3 on 2023-10-01 17:48

import core.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_message_file_name_alter_message_content'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='reference',
            field=models.FileField(blank=True, max_length=255, upload_to=core.models.generate_audio_filename),
        ),
    ]