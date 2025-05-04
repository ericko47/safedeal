import uuid
from django.core.management.base import BaseCommand
from core.models import Item  # Adjust if your model is in a different app

class Command(BaseCommand):
    help = 'Populate item_reference for items that are missing it'

    def handle(self, *args, **kwargs):
        items = Item.objects.filter(item_reference__isnull=True)
        updated = 0

        for item in items:
            item.item_reference = f"SDI-{uuid.uuid4().hex[:8].upper()}"
            item.save()
            updated += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated} item(s).'))
