from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

# def send_custom_email(subject, template_name, context, recipient_list):
#     html_content = render_to_string(template_name, context)
#     email = EmailMultiAlternatives(subject, '', to=[recipient_list])
#     email.attach_alternative(html_content, "text/html")
#     email.send()
    
def send_custom_email(subject, template_name, context, recipient_list):
    message = render_to_string(template_name, context)
    send_mail(
        subject,
        '',
        settings.DEFAULT_FROM_EMAIL,
        recipient_list,
        html_message=message,
    )
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
        
def calculate_fees(amount, fee_percent=5):
    """Calculate platform fee and final payout"""
    fee = (fee_percent / 100) * amount
    payout = amount - fee
    return round(fee, 2), round(payout, 2)

def notify_funding(transaction):
    send_custom_email(
        subject='You have been funded',
        template_name='emails/seller_funded.html',
        context={'transaction': transaction, 'year': timezone.now().year},
        recipient_list=[transaction.seller.email],
    )