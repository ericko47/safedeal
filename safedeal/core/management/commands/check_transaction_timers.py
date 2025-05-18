from decimal import Decimal
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction as db_tx

from core.models import Transaction
from core.utils import send_custom_email   # adjust import to your project

FINE_RATE             = Decimal("0.02")  # 2 %
BUYER_DELAY_HOURS     = 24               # buyer confirmation window
SELLER_DELAY_HOURS    = 24               # seller “arrived” window
BUYER_GRACE_HOURS     = 48               # after arrival → seller may payout
SELLER_GRACE_HOURS    = 48               # after payment → buyer may refund


class Command(BaseCommand):
    help = "Applies fines and sets refund / funding eligibility on old transactions, with notifications."

    def handle(self, *args, **options):
        now = timezone.now()
        self.stdout.write("🚦  Running transaction-timer checks …")

        with db_tx.atomic():

            # 1️⃣  Seller late to mark 'arrived'  ➜ fine 2 %
            late_shipments = Transaction.objects.filter(
                status="shipped",
                shipped_at__lte=now - timedelta(hours=SELLER_DELAY_HOURS),
            )

            for tx in late_shipments:
                if tx.platform_fee == 0:                    # fine only once
                    fine   = tx.amount * FINE_RATE
                    payout = tx.amount - fine
                    tx.platform_fee  = fine
                    tx.seller_payout = payout
                    tx.save(update_fields=["platform_fee", "seller_payout"])

                    # Notify seller
                    send_custom_email(
                        subject="Late-Shipment Fine Applied",
                        template_name="emails/seller_fined.html",
                        context={
                            "transaction": tx,
                            "fine": fine,
                            "payout": payout,
                            "year": now.year,
                        },
                        recipient_list=[tx.seller.email],
                    )

                    self.stdout.write(f"⚠️  Seller fined on TX {tx.transaction_reference}")

            # 2️⃣  Buyer late to confirm delivery  ➜ auto-deliver
            auto_deliver_qs = Transaction.objects.filter(
                status="arrived",
                arrived_at__lte=now - timedelta(hours=BUYER_GRACE_HOURS),
            )

            for tx in auto_deliver_qs:
                tx.status = "delivered"
                tx.save(update_fields=["status"])


                self.stdout.write(f"✅  Auto-delivered TX {tx.transaction_reference}")

            

        self.stdout.write("✅  Timer checks complete.")
     