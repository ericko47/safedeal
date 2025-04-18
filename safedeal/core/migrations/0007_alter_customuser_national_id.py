# Generated by Django 5.2 on 2025-04-16 06:17

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_mpesapaymentlog_securetransaction_mpesa_reference'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='national_id',
            field=models.CharField(blank=True, max_length=20, null=True, unique=True, validators=[django.core.validators.RegexValidator(message='Invalid National ID', regex='^\\d{6,10}$')]),
        ),
    ]
