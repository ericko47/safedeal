# Generated by Django 5.2 on 2025-04-14 05:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_securetransaction_buyer_name_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='MpesaPaymentLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('merchant_request_id', models.CharField(max_length=100)),
                ('checkout_request_id', models.CharField(max_length=100)),
                ('result_code', models.IntegerField()),
                ('result_description', models.TextField()),
                ('amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('phone', models.CharField(blank=True, max_length=15, null=True)),
                ('mpesa_receipt', models.CharField(blank=True, max_length=100, null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.AddField(
            model_name='securetransaction',
            name='mpesa_reference',
            field=models.CharField(blank=True, max_length=100, null=True, unique=True),
        ),
    ]
