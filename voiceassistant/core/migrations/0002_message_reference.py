# Generated by Django 4.1.3 on 2023-09-16 11:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='reference',
            field=models.FileField(blank=True, upload_to='audio/'),
        ),
    ]