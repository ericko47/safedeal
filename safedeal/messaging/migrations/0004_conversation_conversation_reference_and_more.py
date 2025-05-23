# Generated by Django 5.2 on 2025-05-14 06:07

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('messaging', '0003_message_is_read'),
    ]

    operations = [
        migrations.AddField(
            model_name='conversation',
            name='conversation_reference',
            field=models.UUIDField(default=uuid.uuid4),
        ),
        migrations.AddField(
            model_name='conversation',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
