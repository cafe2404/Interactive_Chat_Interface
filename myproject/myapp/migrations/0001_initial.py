# Generated by Django 5.1.7 on 2025-06-18 13:19

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ChatMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.TextField(blank=True)),
                ('file', models.FileField(blank=True, null=True, upload_to='chat_files/')),
                ('sent_at', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'ordering': ['sent_at'],
            },
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('your_name', models.CharField(max_length=255)),
                ('email', models.CharField(max_length=255)),
                ('password', models.CharField(max_length=255)),
                ('your_phone', models.CharField(max_length=255)),
                ('company_name', models.CharField(max_length=255)),
                ('company_tax', models.CharField(max_length=255)),
                ('role', models.CharField(default='user', max_length=255)),
                ('gender', models.CharField(default='Other', max_length=255)),
                ('userImage', models.ImageField(blank=True, null=True, upload_to='')),
                ('refresh_token', models.CharField(blank=True, max_length=255, null=True)),
                ('refresh_expired', models.DateTimeField(blank=True, null=True)),
                ('access_token_issued', models.DateTimeField(blank=True, null=True)),
                ('access_token_expires', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(blank=True, null=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('restored_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ChatFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='chat_files/')),
                ('message', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='files', to='myapp.chatmessage')),
            ],
        ),
        migrations.AddField(
            model_name='chatmessage',
            name='receiver',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='received_messages', to='myapp.user'),
        ),
        migrations.AddField(
            model_name='chatmessage',
            name='sender',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_messages', to='myapp.user'),
        ),
    ]
