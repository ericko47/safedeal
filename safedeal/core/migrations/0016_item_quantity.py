# Generated by Django 5.2 on 2025-05-05 18:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_item_bulk_price_item_is_bulk'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='quantity',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
