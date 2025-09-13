from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import PremiumSubscription, Transaction
from decimal import Decimal, ROUND_HALF_UP

from django.utils import timezone
# from reviews.models import Rating  # adjust if different

def check_premium_eligibility(user):
    """
    Returns a dict with eligibility details and explanation.
    Criteria:
    - At least 5 completed transactions.
    - Delivery rate >= 80%
    - Average rating >= 4.0
    - No recent complaints (customize as needed)
    """

    completed_transactions = Transaction.objects.filter(
        seller=user,
        status='delivered',
    ).count()

    delivered_rate = Transaction.objects.filter(seller=user, shipped_at__isnull=False).count()
    delivery_score = (delivered_rate / completed_transactions * 100) if completed_transactions else 0

    # average_rating = Rating.objects.filter(target_user=user).aggregate(avg=models.Avg('score'))['avg'] or 0

    # Set your own complaint filtering logic if you track complaints
    recent_complaints = 0  # example only

    qualified = (
        completed_transactions >= 5 and
        delivery_score >= 80 and
        # average_rating >= 4.0 and
        recent_complaints == 0
    )

    return {
        "qualified": qualified,
        "reasons": {
            "Transactions completed": f"{completed_transactions} (min: 5)",
            "Delivery success rate": f"{delivery_score:.0f}% (min: 80%)",
            # "Average buyer rating": f"{average_rating:.1f}★ (min: 4.0★)",
            "Recent complaints": f"{recent_complaints} (must be 0)",
        }
    }


def deactivate_expired_subscriptions():
    now = timezone.now()
    expired_subs = PremiumSubscription.objects.filter(is_active=True, expiry_date__lt=now)

    for sub in expired_subs:
        sub.is_active = False
        sub.save()
        sub.user.is_premium = False
        sub.user.save()

    
# def send_custom_email(subject, template_name, context, recipient_list):
#     message = render_to_string(template_name, context)
#     send_mail(
#         subject,
#         '',
#         settings.DEFAULT_FROM_EMAIL,
#         recipient_list,
#         html_message=message,
#     )

def send_custom_email(subject, template_name, context, recipient_list):
    html_content = render_to_string(template_name, context)
    msg = EmailMultiAlternatives(
        subject=subject,
        body='This is an HTML email. Please view it in a client that supports HTML.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipient_list,
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send()

from .models import TransactionStatusLog

def log_transaction_status_change(transaction, new_status, user=None, reason=""):
    if transaction.status != new_status:
        TransactionStatusLog.objects.create(
            transaction=transaction,
            previous_status=transaction.status,
            new_status=new_status,
            changed_by=user,
            reason=reason
        )
        transaction.status = new_status
        transaction.save()
        
def calculate_fees(tx, fee_percent=5, fine_percent=2):
    amount = Decimal(tx.amount)

    fee = (Decimal(fee_percent) / 100) * amount

    # Determine fine automatically
    apply_fine = False
    if tx.status == "paid" and tx.paid_at:
        if timezone.now() - tx.paid_at > timezone.timedelta(hours=24):
            apply_fine = True

    fine = (Decimal(fine_percent) / 100) * amount if apply_fine else Decimal('0.00')

    platform_fee = fee + fine
    payout = amount - platform_fee

    # Round
    platform_fee = platform_fee.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    fine = fine.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    payout = payout.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    return platform_fee, fine, payout

# def calculate_fees(tx, fee_percent=5, fine_percent=2):
#     amount = Decimal(tx.amount)

#     fee = (Decimal(fee_percent) / 100) * amount

#     # Determine fine automatically
#     apply_fine = False

#     # Try to get status from either field
#     status = getattr(tx, "status", None) or getattr(tx, "transaction_status", None)
#     paid_at = getattr(tx, "paid_at", None)

#     if status == "paid" and paid_at:
#         if timezone.now() - paid_at > timezone.timedelta(hours=24):
#             apply_fine = True

#     fine = (Decimal(fine_percent) / 100) * amount if apply_fine else Decimal('0.00')

#     platform_fee = fee + fine
#     payout = amount - platform_fee

#     # Round
#     platform_fee = platform_fee.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
#     fine = fine.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
#     payout = payout.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

#     return platform_fee, fine, payout

def notify_funding(transaction):
    send_custom_email(
        subject='You have been funded',
        template_name='emails/seller_funded.html',
        context={'transaction': transaction, 'year': timezone.now().year},
        recipient_list=[transaction.seller.email],
    )
    
def override_last_crumb(request, name):
    """Replace the last breadcrumb name with something friendlier."""
    trail = request.session.get("navigation_trail", [])
    if trail:
        trail[-1]["name"] = name
        request.session["navigation_trail"] = trail