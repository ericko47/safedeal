from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction as db_tx
from core.models import SecureTransaction
from django.utils import timezone

PLATFORM_FEE_RATE = Decimal("0.05")  # 5% platform fee

class Command(BaseCommand):
    help = "Applies platform fees and calculates seller payout for SecureTransactions."

    def handle(self, *args, **options):
        self.stdout.write("🚦 Running SecureTransaction platform fee update…")

        with db_tx.atomic():
            txs = SecureTransaction.objects.filter(
                transaction_status__in=["shipped", "arrived", "delivered"],
                platform_fee=0
            )

            for tx in txs:
                fee = tx.amount * PLATFORM_FEE_RATE
                payout = tx.amount - fee

                tx.platform_fee = fee
                # If payout field exists, set it here as well, otherwise skip
                if hasattr(tx, 'seller_payout'):
                    tx.seller_payout = payout

                tx.save(update_fields=["platform_fee"] + (["seller_payout"] if hasattr(tx, 'seller_payout') else []))
                self.stdout.write(f"💸 Platform fee set for SecureTX {tx.id}")

        self.stdout.write("✅ SecureTransaction platform fee updates complete.")
