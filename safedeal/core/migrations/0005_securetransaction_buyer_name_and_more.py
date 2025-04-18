# Generated by Django 5.2 on 2025-04-13 06:18

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_securetransaction_transactionout'),
    ]

    operations = [
        migrations.AddField(
            model_name='securetransaction',
            name='buyer_name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='securetransaction',
            name='buyer_phone',
            field=models.CharField(blank=True, max_length=15, null=True, validators=[django.core.validators.RegexValidator(message='Invalid phone number', regex='^\\+?1?\\d{9,15}$')]),
        ),
        migrations.AlterField(
            model_name='securetransaction',
            name='item_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
