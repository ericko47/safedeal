from decimal import Decimal
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction as db_tx

from core.models import Transaction
from core.utils import send_custom_email  # Adjust this import to match your utils path

# Configuration
FINE_RATE             = Decimal("0.02")  # 2% fine
PLATFORM_FEE_RATE     = Decimal("0.05")  # 3% platform fee
SELLER_DELAY_HOURS    = 24               # Seller has 24h after payment to ship
BUYER_GRACE_HOURS     = 48               # Buyer has 48h after arrival to confirm delivery


class Command(BaseCommand):
    help = "Applies fines, calculates payouts, and auto-confirms delivery on transactions."

    def handle(self, *args, **options):
        now = timezone.now()
        self.stdout.write("🚦  Running SafeDeal payout and fine checks…")

        with db_tx.atomic():

            # 1️⃣ Fine sellers who delay shipping
            late_shippers = Transaction.objects.filter(
                status="paid",
                paid_at__lte=now - timedelta(hours=SELLER_DELAY_HOURS),
                platform_fee=0  # Avoid double fines
            )

            for tx in late_shippers:
                fine = tx.amount * FINE_RATE
                fee = tx.amount * PLATFORM_FEE_RATE
                total_deduction = fine + fee
                payout = tx.amount - total_deduction

                tx.platform_fee = fine + fee
                tx.seller_payout = payout
                tx.save(update_fields=["platform_fee", "seller_payout"])

                send_custom_email(
                    subject="Late Shipment Fine Applied",
                    template_name="emails/seller_fined.html",
                    context={
                        "transaction": tx,
                        "fine": fine,
                        "fee": fee,
                        "payout": payout,
                        "year": now.year,
                    },
                    recipient_list=[tx.seller.email],
                )

                self.stdout.write(f"⚠️  Seller fined and fees applied on TX {tx.transaction_reference}")

            # 2️⃣ Apply platform fee for already shipped/delivered transactions (if not already done)
            no_fee_yet = Transaction.objects.filter(
                status__in=["shipped", "arrived", "delivered"],
                platform_fee=0
            )

            for tx in no_fee_yet:
                fee = tx.amount * PLATFORM_FEE_RATE
                payout = tx.amount - fee
                tx.platform_fee = fee
                tx.seller_payout = payout
                tx.save(update_fields=["platform_fee", "seller_payout"])
                self.stdout.write(f"💸 Platform fee set for TX {tx.transaction_reference}")

            # 3️⃣ Auto-confirm delivery if buyer is silent
            auto_deliver_qs = Transaction.objects.filter(
                status="arrived",
                arrived_at__lte=now - timedelta(hours=BUYER_GRACE_HOURS)
            )

            for tx in auto_deliver_qs:
                tx.status = "delivered"
                tx.save(update_fields=["status"])
                self.stdout.write(f"✅ Auto-delivered TX {tx.transaction_reference}")

        self.stdout.write("✅ All checks complete.")
