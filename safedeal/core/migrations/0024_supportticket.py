# Generated by Django 5.2 on 2025-05-15 08:04

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0023_mpesab2cresult_transaction_checkout_request_id_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='SupportTicket',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('issue_type', models.CharField(choices=[('payment', 'Payment Issue'), ('delivery', 'Delivery Issue'), ('dispute', 'Dispute Resolution'), ('verification', 'Verification/ID Issues'), ('account', 'Account Access'), ('other', 'Other')], max_length=50)),
                ('reference', models.CharField(blank=True, max_length=100, null=True)),
                ('message', models.TextField()),
                ('attachment', models.FileField(blank=True, null=True, upload_to='support_attachments/')),
                ('is_resolved', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
