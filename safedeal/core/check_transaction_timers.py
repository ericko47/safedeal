from decimal import Decimal
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction as db_tx

from core.models import Transaction

FINE_RATE = Decimal("0.02")          # 2 % seller fine
BUYER_DELAY_HOURS = 24               # buyer should confirm in 24 h
SELLER_DELAY_HOURS = 24              # seller should mark arrived in 24 h
BUYER_GRACE_HOURS = 48               # after arrival → seller may request payout
SELLER_GRACE_HOURS = 48              # after payment without arrival → buyer may refund


class Command(BaseCommand):
    help = "Applies fines and sets refund / funding eligibility on old transactions."

    def handle(self, *args, **options):
        now = timezone.now()

        self.stdout.write("🚦  Running transaction–timer checks …")

        with db_tx.atomic():

            # 1️⃣  Seller late to mark 'shipped'  ➜ fine 2 %
            late_shipments = Transaction.objects.filter(
                status="shipped",
                shipped_at__lte=now - timedelta(hours=SELLER_DELAY_HOURS),
            )
            for tx in late_shipments:
                if tx.platform_fee == 0:                         # fine only once
                    fine = tx.amount * FINE_RATE
                    tx.platform_fee = fine
                    tx.seller_payout = tx.amount - fine
                    tx.save(update_fields=["platform_fee", "seller_payout"])
                    self.stdout.write(
                        f"⚠️  Seller fine applied (2 %) on TX {tx.transaction_reference}"
                    )

            # 2️⃣  Buyer late to confirm delivery  ➜ flag seller payout allowed
            arrived_48h = Transaction.objects.filter(
                status="arrived",
                arrived_at__lte=now - timedelta(hours=BUYER_GRACE_HOURS),
            )
            updated = arrived_48h.update(status="delivered")     # auto-deliver
            if updated:
                self.stdout.write(f"✅  Auto-delivered {updated} transaction(s)")
                #email
            # 3️⃣  Paid > 48 h with no shipment  ➜ buyer may refund
            unpaid_ship = Transaction.objects.filter(
                status="paid",
                paid_at__lte=now - timedelta(hours=SELLER_GRACE_HOURS),
            )
            for tx in unpaid_ship:
                tx.status = "refund_eligible"
                tx.save(update_fields=["status"])
                self.stdout.write(
                    f"💰  TX {tx.transaction_reference} marked refund-eligible"
                )

        self.stdout.write("✅  Timer checks complete.")

curl -Method POST http://127.0.0.1:8000//mpesa/callback/ `
     -Headers @{ "Content-Type" = "application/json" } `
     -Body @'
{
  "Body": {
    "stkCallback": {
      "MerchantRequestID": "Testwithshem",
      "CheckoutRequestID": "67890",
      "ResultCode": 0,
      "ResultDesc": "Success",
      "CallbackMetadata": {
        "Item": [
          { "Name": "Amount", "Value": 50000 },
          { "Name": "MpesaReceiptNumber", "Value": "ABC1DQ456" },
          { "Name": "PhoneNumber", "Value": 254740364413 },
          { "Name": "AccountReference", "Value": "971c7da403df" }
        ]
      }
    }
  }
}
'@
