# Generated by Django 5.2 on 2025-05-19 11:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0029_transaction_hold_payout'),
    ]

    operations = [
        migrations.AlterField(
            model_name='securetransaction',
            name='transaction_status',
            field=models.CharField(choices=[('pending', 'Pending'), ('paid', 'Paid'), ('shipped', 'Shipped'), ('delivered', 'Delivered'), ('disputed', 'Disputed'), ('arrived', 'arrived'), ('cancelled', 'Cancelled')], default='pending', max_length=20),
        ),
    ]
