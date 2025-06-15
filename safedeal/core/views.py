from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from .forms import CustomUserCreationForm, UserProfileForm, ItemForm, DisputeForm, TransactionOutForm, ItemReportForm, ShippingForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from .models import Item , ItemImage, Transaction, TransactionDispute, CustomUser, ItemReport, Wishlist, DisputeEvidence, TransactionStatusLog, SupportTicket
import uuid
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.http import HttpResponseForbidden
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from mpesa.utils import lipa_na_mpesa, initiate_b2c_payment, query_stk_status
from core.utils import send_custom_email, log_transaction_status_change, calculate_fees, notify_funding
from django.utils.timezone import now
from django.core.mail import send_mail
from django.conf import settings
from .models import PremiumSubscription

from django.contrib.admin.views.decorators import staff_member_required
from .utils import check_premium_eligibility 
from .forms import DeliveryAgentForm, DeliveryOrganizationForm
from .models import DeliveryOrganization, DeliveryAgent

from django.db import IntegrityError

def register_delivery_agent(request):
    if request.method == "POST":
        agent_form = DeliveryAgentForm(request.POST, request.FILES)
        org_form = DeliveryOrganizationForm(request.POST, request.FILES)

        registering_as = request.POST.get('registering_as')

        # Check if the user already has an agent profile
        if DeliveryAgent.objects.filter(user=request.user).exists():
            messages.error(
                request,
                "You already have a delivery agent profile. If you'd like to register as an organization instead, please contact support for assistance."
            )
            return redirect('dashboard')  # or stay on the same page

        if registering_as == "individual" and agent_form.is_valid():
            # Save individual agent
            agent = agent_form.save(commit=False)
            agent.user = request.user
            agent.agent_type = "individual"
            agent.save()
            messages.success(request, "You have successfully registered as an Individual Delivery Agent.")
            return redirect('dashboard')

        elif registering_as == "organization" and org_form.is_valid() and agent_form.is_valid():
            # Check if organization exists
            org_name = org_form.cleaned_data['name']
            if DeliveryOrganization.objects.filter(name__iexact=org_name).exists():
                messages.error(request, "An organization with that name already exists.")
            else:
                try:
                    # Save organization
                    organization = org_form.save()

                    # Save first agent linked to org
                    agent = agent_form.save(commit=False)
                    agent.user = request.user
                    agent.agent_type = "organization"
                    agent.organization = organization
                    agent.save()

                    messages.success(
                        request,
                        f"Organization '{organization.name}' created and linked to your agent profile."
                    )
                    return redirect('dashboard')

                except IntegrityError:
                    messages.error(
                        request,
                        "There was a problem creating your agent profile. You may already have an existing one."
                    )
                    return redirect('dashboard')

    else:
        agent_form = DeliveryAgentForm()
        org_form = DeliveryOrganizationForm()

    context = {
        'agent_form': agent_form,
        'org_form': org_form
    }
    return render(request, 'delivery/register_delivery_agent.html', context)



@login_required
def upgrade_to_premium(request):
    user = request.user
    
    required_fields = [
    user.national_id,
    user.phone_number,
    user.current_location,
    user.permanent_address,
    user.account_type,
    user.profile_picture,
    user.national_id_picture,
    ]

    if not all(required_fields):
        messages.warning(request, "Please complete your profile before uprading.")
        return redirect('update_profile') 
    eligibility = check_premium_eligibility(user)
    status = PremiumSubscription.objects.filter(user=user).first()
    if request.method == 'POST':
        if not user.national_id:
            messages.error(request, "You must update your national ID before upgrading.")
            return redirect('update_profile')

        phone = user.phone_number
        amount = 499
        account_reference = user.national_id
        transaction_desc = f"Premium Upgrade for {user.get_full_name()}"

        response = lipa_na_mpesa(
            phone_number=phone,
            amount=amount,
            account_reference=account_reference,
            transaction_desc=transaction_desc
        )

        if response.get('ResponseCode') == "0":
            messages.success(request, "STK Push sent. Complete the payment on your phone.")
        else:
            messages.error(request, "Failed to initiate payment. Try again later.")

        return redirect('upgrade_to_premium')

    return render(request, 'core/upgrade_to_premium.html', {
        "eligibility": eligibility,
        "status": status,
    })

@login_required
def support(request):
    if request.method == 'POST':
        issue_type = request.POST.get('issue_type')
        reference = request.POST.get('reference')
        message = request.POST.get('message')
        attachment = request.FILES.get('attachment')
        user = request.user

        ticket = SupportTicket.objects.create(
            user=user,
            issue_type=issue_type,
            reference=reference,
            message=message, 
            attachment = attachment
        )

        # Email notification
        send_mail(
            subject=f"[SafeDeal Support] New Ticket from {user.username}",
            message=f"Issue: {ticket.get_issue_type_display()}\n"
                    f"Reference: {ticket.reference or 'N/A'}\n"
                    f"Message:\n{ticket.message}\n\n"
                    f"Submitted by: {user.username} ({user.email})",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[admin[1] for admin in settings.ADMINS],
            fail_silently=True,
        )

        messages.success(request, "Your support request has been submitted. We’ll get back to you shortly.")
        return redirect('support')
    else:    
        tickets = SupportTicket.objects.filter(user=request.user).order_by('-created_at')
        return render(request, 'core/support.html', {'tickets': tickets})


@login_required
def confirm_delivery(request, transaction_reference):
    transaction = get_object_or_404(Transaction, transaction_reference=transaction_reference)

    if request.user != transaction.buyer:
        return HttpResponseForbidden("You are not authorized to confirm this delivery.")

    if request.method == 'POST':
        if transaction.status == 'shipped':
            transaction.status = 'delivered'
            transaction.save()

            # Mark item as unavailable
            item = transaction.item
            item.is_available = False
            item.save()
            
            messages.success(request, "Delivery confirmed. Funds will now be released to the seller.")
            send_custom_email(
                subject='Delivery Confirmed by Buyer',
                template_name='emails/delivery_confirmed.html',
                context={
                    'transaction': transaction,
                    'year': timezone.now().year,
                },
                recipient_list=[transaction.seller.email],
            )
        else:
            messages.warning(request, "This transaction is not in a 'shipped' state.")

    return redirect('transaction_detail', transaction_reference=transaction.transaction_reference)

@staff_member_required
def fundable_transactions(request):
    transactions = Transaction.objects.filter(
        status="delivered",
        is_funded=False,
        hold_payout=False
    ).order_by("-created_at")

    return render(request, "admin/fundable_transactions.html", {
        "transactions": transactions
    })
@staff_member_required
def toggle_hold_payout(request, transaction_id):
    tx = get_object_or_404(Transaction, id=transaction_id)
    tx.hold_payout = not tx.hold_payout
    tx.save(update_fields=["hold_payout"])

    state = "paused" if tx.hold_payout else "resumed"
    messages.info(request, f"Payout {state} for TX #{tx.transaction_reference}.")
    return redirect("fundable_transactions")
@login_required
def request_refund(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, buyer=request.user)

    if transaction.can_buyer_request_refund():
        transaction.status = 'Refund Requested'
        transaction.save()

        send_custom_email(
            subject='Refund Requested by Buyer',
            template_name='emails/refund_requested.html',
            context={
                'transaction': transaction,
                'year': timezone.now().year,
            },
            recipient_list=[transaction.seller.email],
        )
        response = initiate_b2c_payment(
            phone_number=transaction.seller.phone_number,
            amount=transaction.seller_payout, # Adjust as needed.....
            transaction_id=transaction.id
        )

        messages.success(request, "Refund request sent to seller.")
    else:
        messages.error(request, "You are not eligible to request a refund yet.")

    return redirect('transaction_detail', transaction_id=transaction.id)


@staff_member_required
def fund_seller(request, transaction_id):
    tx = get_object_or_404(Transaction, id=transaction_id)

    if not tx.status == "delivered" or tx.is_funded or tx.hold_payout:
        messages.warning(request, "This transaction is not eligible for funding.")
        return redirect("fundable_transactions")

    fee, payout = calculate_fees(tx.amount)
    
    # Save these before sending payment
    tx.platform_fee = fee
    tx.seller_payout = payout
    response = initiate_b2c_payment(
        phone_number=tx.seller.phone_number,
        amount=tx.seller_payout,
        transaction_reference=tx.transaction_reference
    )

    if response.get("ResultCode") == 0:
        tx.is_funded = True
        tx.funded_at = timezone.now()
        tx.save(update_fields=["is_funded", "funded_at"])
        messages.success(request, f"Successfully funded seller for TX #{tx.transaction_reference}.")
    else:
        messages.error(request, f"Failed to fund: {response.get('ResultDesc')}")

    return redirect("fundable_transactions")

@login_required
def request_funding(request, transaction_reference):
    tx = get_object_or_404(Transaction, transaction_reference=transaction_reference, seller=request.user)
  
    if not tx.can_seller_request_funding():
        messages.error(request, "You’re not yet eligible to request payout.")
        return redirect('transaction_detail', transaction_reference=transaction_reference)

    # initiate B2C to seller
    response = initiate_b2c_payment(
        phone_number=tx.seller.phone_number,
        amount=tx.seller_payout,
        transaction_id=tx.id
    )
    if response["ResponseCode"] == "0":
        tx.is_funded = True
        tx.funded_at = timezone.now()
        tx.save()
        messages.success(request, "Payout requested. Funds will reach your M-PESA shortly.")
    else:
        messages.error(request, "Failed to initiate payout. Please contact support.")

    return redirect('transaction_detail', transaction_reference=transaction_reference)


@login_required
def mark_arrived(request, transaction_reference):
    transaction = get_object_or_404(Transaction, transaction_reference=transaction_reference)

    if request.user != transaction.seller and request.user != transaction.delivery_agent.user:
        return HttpResponseForbidden("You are not authorized to mark this item as arrived.")

    if transaction.status != 'shipped':
        messages.warning(request, "This transaction is not in a 'shipped' state.")
        return redirect('transaction_detail', transaction_reference=transaction_reference)

    transaction.status = 'arrived'
    transaction.arrived_at = timezone.now()
    transaction.save()

    messages.success(request, "Item marked as arrived. Buyer has 48h to confirm delivery.")

    send_custom_email(
        subject='Item Arrival Notification',
        template_name='emails/item_arrived.html',
        context={
            'transaction': transaction,
            'year': timezone.now().year,
        },
        recipient_list=[transaction.buyer.email],
    )

    return redirect('transaction_detail', transaction_reference=transaction_reference)

def mark_securearrived(request, mpesa_reference):
    transaction = get_object_or_404(SecureTransaction, mpesa_reference=mpesa_reference)

    if request.user != transaction.seller and request.user != transaction.delivery_agent.user:
        return HttpResponseForbidden("You are not authorized to mark this item as arrived.")

    if transaction.transaction_status != 'shipped':
        messages.warning(request, "This transaction is not in a 'shipped' state.")
        return redirect('external_transaction_detail', mpesa_reference=mpesa_reference)

    transaction.transaction_status = 'arrived'
    transaction.arrived_at = timezone.now()
    transaction.save()

    messages.success(request, "Item marked as arrived. Buyer will be contacted shortly.")

    send_custom_email(
        subject='Item Arrival Notification',
        template_name='emails/item_arrived.html',
        context={
            'transaction': transaction,
            'year': timezone.now().year,
        },
        recipient_list=[transaction.buyer_email],
    )

    return redirect('dashboard')

@login_required
def cancel_transaction(request, transaction_reference):
    transaction = get_object_or_404(Transaction, transaction_reference=transaction_reference)

    if request.user != transaction.buyer:
        return HttpResponseForbidden("You are not authorized to cancel this transaction.")

    if request.method == 'POST':
        if transaction.status == "pending":
            transaction.status = "cancelled"
            transaction.save(update_fields=["status"])

            # release item back to listings
            item = transaction.item
            if not item.is_available:
                item.is_available = True
                item.save(update_fields=["is_available"])
            send_custom_email(
                subject="Buyer cancelled the order",
                template_name="emails/tx_cancelled_by_buyer.html",
                context={"transaction": transaction},
                recipient_list=[transaction.seller.email],
            )
            messages.success(request, "Transaction cancelled successfully. Item is now available for sale again.")  
        else:
            messages.warning(request, "Only pending transactions can be cancelled.")
    return redirect('transaction_detail', transaction_reference=transaction.transaction_reference)


@login_required
def raise_dispute(request, transaction_reference):
    transaction = get_object_or_404(Transaction, transaction_reference=transaction_reference, buyer=request.user)

    if transaction.status not in ['paid', 'shipped']:
        messages.warning(request, "You can only raise a dispute for paid or shipped transactions.")
        return redirect('dashboard')

    # Prevent duplicate disputes
    if hasattr(transaction, 'transactiondispute'):
        messages.info(request, "A dispute has already been raised for this transaction.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = DisputeForm(request.POST)
        if form.is_valid():
            # Update and log transaction status
            previous_status = transaction.status
            transaction.status = 'disputed'
            transaction.save()

            log_transaction_status_change(
                transaction,
                new_status='disputed',
                user=request.user,
                reason=f'Dispute raised by buyer (was {previous_status})'
            )

            # Create the dispute record
            dispute = TransactionDispute.objects.create(
                transaction=transaction,
                reason=form.cleaned_data['reason'],
                additional_details=form.cleaned_data['additional_details'],
                created_at=timezone.now()
            )

            files = request.FILES.getlist('evidence_files')
            if files:
                for file in files:
                    if file.size > 5 * 1024 * 1024:  # 5MB limit
                        messages.error(request, f"{file.name} is too large (max 5MB).")
                        return render(request, 'core/raise_dispute.html', {'form': form, 'transaction': transaction})
                    if not file.content_type.startswith('image/'):
                        messages.error(request, f"{file.name} is not a valid image.")
                        return render(request, 'core/raise_dispute.html', {'form': form, 'transaction': transaction})

                    DisputeEvidence.objects.create(dispute=dispute, file=file)

            send_custom_email(
                subject='Dispute Raised',
                template_name='emails/dispute_raised.html',
                context={
                    'transaction': transaction,
                    'reason': form.cleaned_data['reason'],
                    'additional_details': form.cleaned_data['additional_details'],
                },
                recipient_list=[transaction.seller.email],
            )

            messages.success(request, "Dispute raised successfully. Our team will review it.")
            return redirect('dashboard')
    else:
        form = DisputeForm()

    return render(request, 'core/raise_dispute.html', {
        'form': form,
        'transaction': transaction
    })

@login_required
def ship_item(request, transaction_reference):
    transaction = get_object_or_404(Transaction, transaction_reference=transaction_reference, seller=request.user)
    if transaction.status != 'paid':
        messages.error(request, "Item cannot be shipped in its current state.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = ShippingForm(request.POST, request.FILES, instance=transaction)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.status = 'shipped'
            transaction.shipped_at = timezone.now()
            transaction.save()
            # Send email to buyer
            send_custom_email(  
                subject='Item Shipped',
                template_name='emails/item_shipped.html',
                context={
                    'buyer': transaction.buyer,
                    'item': transaction.item,
                    'shipping_evidence': form.cleaned_data['shipping_evidence'],
                },
                recipient_list=[transaction.buyer.email],
            )
            messages.success(request, "Item marked as shipped.")
            return redirect('dashboard')
    else:
        form = ShippingForm(instance=transaction)

    return render(request, 'core/ship_item.html', {'form': form, 'transaction': transaction})

@login_required
def ship_item_by_mpesa(request, mpesa_reference):
    tx = get_object_or_404(
        SecureTransaction,
        mpesa_reference=mpesa_reference,
        seller=request.user,
    )

    # guard clauses ----------------------------------------------------------------
    if tx.transaction_status != "paid":
        messages.error(
            request,
            "This order is not in a state that can be marked as 'shipped'.",
        )
        return redirect("dashboard")

    # POST  -------------------------------------------------------------------------
    if request.method == "POST":
        # update
        tx.transaction_status = "shipped"
        tx.shipped_at = timezone.now()
        tx.save(update_fields=["transaction_status", "shipped_at", "updated_at"])

        # notify buyer
        send_custom_email(
            subject="Your item has been shipped!",
            template_name="emails/item_shipped_external.html",
            context={"transaction": tx},
            recipient_list=[tx.buyer_email],
        )

        messages.success(request, "Item marked as shipped and buyer notified.")
        return redirect("dashboard")
    return render(
        request,
        "core/confirm_ship_external.html",
        {"transaction": tx},
    )



def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Prevent login until verified
            user.save()

            # Generate token and UID
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            # Build activation link
            activation_url = request.build_absolute_uri(
                reverse('activate_account', kwargs={'uidb64': uid, 'token': token})
            )

            # Send activation email
            send_custom_email(
                subject='Activate your SafeDeal account',
                template_name='emails/welcome_email.html',
                context={'user': user, 'activation_url': activation_url},
                recipient_list=[user.email],
            )

            messages.info(request, 'Registration successful! Please check your email to activate your account.')
            return redirect('login')  # Wait until verification
    else:
        form = CustomUserCreationForm()

    return render(request, 'core/register.html', {'form': form})

def activate_account(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()

        # Fix for multiple backends
        user.backend = 'allauth.account.auth_backends.AuthenticationBackend'
        login(request, user)

        messages.success(request, 'Your email has been verified and your account is now active! Please Update your account to enjoy our services with ease.')
        return redirect('dashboard')
    else:
        messages.error(request, 'Activation link is invalid or expired.')
        return redirect('login')

def logout_view(request):
    # Log out the user
    logout(request)    
    # Redirect the user to the homepage or login page
    return redirect('index') 

def index(request):
    return render(request, 'core/index.html')

def faq(request):
    return render(request, 'core/faq.html')

def login_view(request):
    next_url = request.GET.get('next', '')
    if next_url:
        messages.info(request, "Please log in to continue.")
   
    return render(request, 'core/login.html')


@login_required
def dashboard_view(request):
    user = request.user
    buyer_transactions = Transaction.objects.filter(buyer=user).order_by('-created_at')[:10]
    seller_transactions = Transaction.objects.filter(seller=user).order_by('-created_at')[:10]
    seller_securetransactions = SecureTransaction.objects.filter(seller=user).order_by('-created_at')[:10]
    
    return render(request, 'core/dashboard.html', {
        'buyer_transactions': buyer_transactions,
        'seller_transactions': seller_transactions,
        'seller_securetransactions': seller_securetransactions,
    })
@login_required
def all_purchases_view(request):
    transactions = Transaction.objects.filter(buyer=request.user).order_by('-created_at')
    return render(request, 'core/all_purchases.html', {'transactions': transactions})


@login_required
def all_sales_view(request):
    transactions = Transaction.objects.filter(seller=request.user).order_by('-created_at')
    return render(request, 'core/all_sales.html', {'transactions': transactions})



@login_required
def profile_view(request):
    return render(request, 'core/profile.html')

@login_required
def my_items_view(request):    
    user_items = Item.objects.filter(seller=request.user, is_available=True).order_by('-created_at')
    return render(request, 'core/my-items.html', {'items': user_items})


@login_required
def delete_item_view(request, item_reference):
    item = get_object_or_404(Item, item_reference= item_reference, seller=request.user)
    if request.method == 'POST':
        item.delete()
        messages.success(request, "Item deleted successfully.")
        return redirect('my_items')
    return render(request, 'core/confirm_delete.html', {'item': item})

from django.contrib.auth.decorators import user_passes_test
@login_required
@user_passes_test(lambda u: u.is_staff)
def reported_items_view(request):
    reports = ItemReport.objects.select_related('item', 'reported_by', 'item__seller').order_by('-timestamp')

    if request.method == 'POST':
        action = request.POST.get('action')
        report_id = request.POST.get('report_id')
        report = get_object_or_404(ItemReport, id=report_id)

        if action == 'delete_item':
            item = report.item
            item.delete()
            report.reviewed = True
            report.save()
            messages.success(request, f"Item '{item.title}' deleted and report marked as reviewed.")

        elif action == 'contact_users':
            seller = report.item.seller
            reporter = report.reported_by

            # Example email logic (adjust as needed)
            send_mail(
                subject="Item Report Notice",
                message=f"The item '{report.item.title}' was reported for the following reason: {report.reason}",
                from_email=None,
                recipient_list=[seller.email, reporter.email]
            )
            messages.success(request, "Emails sent to reporter and seller.")

        elif action == 'mark_reviewed':
            report.reviewed = True
            report.save()
            messages.success(request, "Report marked as reviewed.")

        return redirect('reported_items')

    return render(request, 'admin/reported_items.html', {'reports': reports})

@login_required
def update_profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()            
            messages.success(request, 'Your profile was updated successfully!')
            return redirect('profile')  # Redirect to profile page after updating
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, 'core/update_profile.html', {'form': form})


from django.db.models import Q, Exists, OuterRef, BooleanField, ExpressionWrapper
BLOCKING_STATES = ["paid", "shipped", "arrived", "delivered", "completed"]
def browse_view(request):
    
    category_filter = request.GET.get("category", "")
    query           = request.GET.get("q", "")

    # ── Sub-query: does this item have a blocking transaction? ────────────────
    blocking_tx = Transaction.objects.filter(
        item      = OuterRef("pk"),
        status__in= BLOCKING_STATES,
    )

    # Base queryset
    items = (
        Item.objects
            .filter(is_available=True)
            .annotate(
                seller_is_premium = ExpressionWrapper(
                    Q(seller__is_premium=True), output_field=BooleanField()
                ),
                has_blocking_tx   = Exists(blocking_tx),
            )
            .filter(has_blocking_tx=False)            # 💡 hide blocked ones
            .order_by("-seller_is_premium", "-created_at")
    )

    # Optional filters --------------------------------------------------------
    if category_filter:
        items = items.filter(category=category_filter)

    if query:
        items = items.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )

    return render(
        request,
        "core/browse.html",
        {
            "items"            : items,
            "categories"       : Item.CATEGORY_CHOICES,
            "selected_category": category_filter,
            "search_query"     : query,
        },
    )

blocking_tx = Transaction.objects.filter(
        item_id=OuterRef('pk'),
        status__in=['paid', 'shipped', 'arrived', 'delivered']
    )

def search_items(request):
    query = request.GET.get('q', '').strip()

    # Base queryset: only items **without** a blocking transaction
    safe_items = Item.objects.annotate(
        has_blocking_tx=Exists(blocking_tx)
    ).filter(
        is_available=True,        # still unsold
        has_blocking_tx=False     # not tied up in another deal
    )

    exact_matches   = safe_items.none()
    keyword_matches = safe_items.none()

    if query:
        exact_matches = safe_items.filter(item_reference__iexact=query)

        keyword_matches = safe_items.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        ).exclude(item_reference__iexact=query)

    context = {
        "query": query,
        "exact_matches": exact_matches,
        "keyword_matches": keyword_matches,
    }
    return render(request, "core/search_results.html", context)

def escrow_view(request):
    return render(request, 'core/escrow.html')

@login_required
def post_item_view(request):
    user = request.user

    required_fields = [
        user.national_id,
        user.phone_number,
        user.current_location,
        user.permanent_address,
        user.account_type,
        user.profile_picture,
        user.national_id_picture,
    ]

    if not all(required_fields):
        messages.warning(request, "Please complete your profile before posting an item.")
        return redirect('update_profile') 

    if not user.is_verified:
        messages.warning(request, "Please wait for admin to verify your details or check your email for admin comments on your account.")
        return redirect('dashboard')

    # Check current item count
    active_count = Item.objects.filter(seller=user, is_available=True).count()
    can_post = True
    remaining_slots = None

    if not user.is_premium:
        remaining_slots = 5 - active_count
        if active_count >= 5:
            can_post = False

    if request.method == 'POST':
        if not can_post:
            messages.error(request, "Free users can only list up to 5 items. Upgrade to Premium to list more.")
            return redirect('upgrade_to_premium')

        form = ItemForm(request.POST, request.FILES)
        files = request.FILES.getlist('images')

        if form.is_valid():
            item = form.save(commit=False)
            item.seller = user

            if item.is_bulk and not user.is_premium:
                messages.error(request, "Bulk listings are only available to Premium sellers. Please uncheck 'bulk' or upgrade your account.")
                return render(request, 'core/post-item.html', {'form': form, 'can_post': can_post, 'remaining_slots': remaining_slots})

            for f in files:
                if f.size > 5 * 1024 * 1024:
                    messages.error(request, f"{f.name} is too large (max 5MB).")
                    return render(request, 'core/post-item.html', {'form': form, 'can_post': can_post, 'remaining_slots': remaining_slots})
                if not f.content_type.startswith('image/'):
                    messages.error(request, f"{f.name} is not a valid image.")
                    return render(request, 'core/post-item.html', {'form': form, 'can_post': can_post, 'remaining_slots': remaining_slots})

            item.save()
            for f in files:
                ItemImage.objects.create(item=item, image=f)

            messages.success(request, "Item posted successfully!")
            return redirect('post_item')
        else:
            messages.error(request, "There was an error with your form.")
    else:
        form = ItemForm()

    return render(request, 'core/post-item.html', {
        'form': form,
        'can_post': can_post,
        'remaining_slots': remaining_slots,
    })


def item_detail(request, item_reference):   
    item = get_object_or_404(Item, item_reference=item_reference)
    in_wishlist = False

    if request.user.is_authenticated:
        in_wishlist = Wishlist.objects.filter(user=request.user, item=item).exists()

    return render(request, 'core/viewitem.html', {
        'item': item,
        'in_wishlist': in_wishlist,
    })




@login_required
def report_item(request, item_reference):
    user = request.user
    # Check for essential profile fields
    required_fields = [
        user.national_id,
        user.phone_number,
        user.current_location,
        user.permanent_address,
        user.account_type,
        user.profile_picture,
        user.national_id_picture,
    ]

    if not all(required_fields):
        messages.warning(request, "Please complete your profile before you can report this item.")
        return redirect('update_profile')
    item = get_object_or_404(Item, item_reference=item_reference)

    if request.method == 'POST':
        form = ItemReportForm(request.POST)
        if form.is_valid():
            reason = form.cleaned_data['reason']
            report, created = ItemReport.objects.get_or_create(
                item=item,
                reported_by=request.user,
                defaults={'reason': reason}
            )
            if created:
                messages.success(request, 'Item reported successfully.')
            else:
                messages.info(request, 'You have already reported this item.')
            return redirect('item_detail', item_reference=item.item_reference)
    else:
        form = ItemReportForm()

    return render(request, 'core/report_item.html', {'form': form, 'item': item})

@login_required
def toggle_wishlist(request, item_reference):
    item = get_object_or_404(Item, item_reference =item_reference)
    wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, item=item)

    if not created:
        wishlist_item.delete()

    return redirect('item_detail', item_reference=item.item_reference)

@login_required
def view_wishlist(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('item')

    context = {
        'wishlist_items': wishlist_items
    }

    return render(request, 'core/view_wishlist.html', context)

@login_required
def user_transactions_view(request):
    transactions = Transaction.objects.filter(buyer=request.user).order_by('-created_at')
    return render(request, 'core/my_transactions.html', {'transactions': transactions})


def privacy_view(request): 
    return render(request, 'core/privacy.html')

def terms_view(request):
    return render(request, 'core/terms.html')

def about_view(request):
    return render(request, 'core/about.html')







#hanling guest transaction
@login_required
def generate_transaction_out(request):
    if request.method == 'POST':
        form = TransactionOutForm(request.POST)
        if form.is_valid():
            transaction_out = form.save(commit=False)
            transaction_out.seller = request.user  # link to current logged-in seller (if you need)
            transaction_out.save()
            return redirect('transaction_out_detail', pk=transaction_out.pk)
    else:
        form = TransactionOutForm()

    return render(request, 'core/generate_transaction_out.html', {'form': form})
     

def external_transaction_detail(request, transaction_id):
    tx = get_object_or_404(SecureTransaction, id=transaction_id)
    timeline = [
        ("Paid",      tx.transaction_status in ["paid", "shipped", "delivered", "arrived"]),
        ("Shipped",   tx.transaction_status in ["shipped", "delivered", "arrived"]),
        ("Arrived", tx.transaction_status in ["delivered", "arrived"]),
        ("Delivered", tx.transaction_status == "delivered"),
    ]
    return render(request, 'core/external_transaction_detail.html', {
        'transaction': tx,
        "timeline": timeline
    })


def initiate_payment(request, transaction_id):
    transaction = get_object_or_404(SecureTransaction, id=transaction_id)

    if request.method == "POST":
        # Generate a unique reference
        if not transaction.mpesa_reference:
            transaction.mpesa_reference = f"SD-{uuid.uuid4().hex[:10]}"
            transaction.save()
        
        phone = transaction.buyer_phone
        amount = transaction.amount

        # Send to M-PESA with this reference
        response = lipa_na_mpesa(
            phone_number=phone,
            amount=amount,
            account_reference=transaction.mpesa_reference,  # Pass here
            transaction_desc=f"Payment for {transaction.mpesa_reference}"
        )

        print("STK Push Response:", response)  # Optional debug

        # Optionally set status here
        transaction.transaction_status = 'pending'
        transaction.save()

        messages.success(request, 'Payment initiated. You will receive an M-PESA prompt shortly.')

        return render(request, 'core/payment_initiated.html', {'transaction': transaction})
    

from .forms import SecureTransactionForm

active_tx = Transaction.objects.filter(
        item_id=OuterRef("pk"),
        status__in=["paid", "shipped", "arrived", "delivered"]
)

@login_required
def create_secure_transaction(request):
    user = request.user

    if not user.is_verified:
        messages.warning(
            request,
            "Your account awaits verification. Check your email for admin comments or contact support."
        )
        return redirect("dashboard")

    if request.method == "POST":
        form = SecureTransactionForm(request.POST)

        if form.is_valid():
            tx = form.save(commit=False)
            tx.seller = user

            item_ref = form.cleaned_data.get("item_reference")
            if item_ref:
                # fetch the seller’s item and annotate whether it’s ‘locked’
                try:
                    item_qs = Item.objects.filter(
                        item_reference=item_ref,
                        seller=user
                    ).annotate(has_active_tx=Exists(active_tx))

                    item = item_qs.get()
                    if (not item.is_available) or item.has_active_tx:
                        form.add_error(
                            "item_reference",
                            "This item is currently not eligible for a new transaction."
                        )
                        raise ValueError  # jump to re-render form

                    # ✅ safe – populate details
                    tx.item_name   = item.title
                    tx.amount      = item.price
                    tx.description = item.description

                except Item.DoesNotExist:
                    form.add_error(
                        "item_reference",
                        "Invalid reference — item not found in your inventory."
                    )
                except ValueError:
                    pass  # form already has an error, just re-render

            # If no errors were injected, go ahead and save
            if not form.errors:
                tx.save()
                messages.success(request, "Transaction link created successfully!")
                return redirect("transaction_success", transaction_id=tx.id)

    else:
        # GET – pre-fill ref if it came via query-string
        ref = request.GET.get("item_reference")
        form = SecureTransactionForm(initial={"item_reference": ref} if ref else None)

    return render(request, "core/create_transaction.html", {"form": form})

# core/views.py  (or wherever your view lives)
import io, base64, qrcode
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives

@login_required
def transaction_success(request, transaction_id):
    transaction = get_object_or_404(
        SecureTransaction,
        id=transaction_id,
        seller=request.user
    )

    secure_link = request.build_absolute_uri(transaction.get_secure_link())

    # --- 1. generate QR code ---
    qr = qrcode.make(secure_link)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    # --- 2. email buyer with link + QR ---
    subject = "Secure Purchase Link for your order via SafeDeal"
    context = {
        "buyer_name": transaction.buyer_name or "there",
        "seller": request.user,
        "item_name": transaction.item_name or "your item",
        "amount": transaction.amount,
        "secure_link": secure_link,
    }

    html_body = render_to_string(
        "emails/secure_link_to_buyer.html", context
    )
    text_body = render_to_string(
        "emails/secure_link_to_buyer.txt", context
    )

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[transaction.buyer_email],
    )
    email.attach_alternative(html_body, "text/html")
    email.send(fail_silently=True)   # swap to False in staging/dev

    # --- 3. render success page for seller ---
    return render(
        request,
        "core/transaction_success.html",
        {
            "transaction": transaction,
            "secure_link": secure_link,
            "qr_code": qr_base64,
        },
    )


@login_required
def place_order(request, item_reference): 
    user = request.user
    # Check for essential profile fields
    required_fields = [
        user.national_id,
        user.phone_number,
        user.current_location,
        user.permanent_address,
        user.account_type,
        user.profile_picture,
        user.national_id_picture,
    ]

    if not all(required_fields):
        messages.warning(request, "Please complete your profile before you can place an order.")
        return redirect('update_profile')
    item = get_object_or_404(Item, item_reference=item_reference)
    if item.seller == request.user:
        messages.error(request, "You cannot buy your own item.")
        return redirect('item_detail', item_reference=item.item_reference)

    if request.method == 'POST':
        transaction_ref = str(uuid.uuid4()).replace('-', '')[:12]  # Unique 12-char ref
        delivery_address = request.POST.get('delivery_address')

        # Create transaction with status 'pending'
        transaction = Transaction.objects.create(
            buyer=request.user,
            seller=item.seller,
            item=item,
            amount=item.price,
            status='pending',
            delivery_address=delivery_address,
            transaction_reference=transaction_ref
        )

        # Trigger STK Push
        phone = request.user.phone_number  # Ensure this exists
        response = lipa_na_mpesa(
            phone_number=phone,
            amount=10, #item.price,
            account_reference=transaction_ref,
            transaction_desc=f"Purchase {item.item_reference}"
        )
        if response.get("ResponseCode") == "0":
            transaction.checkout_request_id = response.get("CheckoutRequestID")
            transaction.save()
            messages.success(request, "Payment request sent. Check your phone.")
            
            return redirect('transaction_detail', transaction.transaction_reference)

        else:
            #messages.error(request, "Failed to initiate payment. Try again.")
            # Add this debug print or message
            messages.error(request, f"Failed to initiate payment: {response}")
            # Optional: print to console or log
            print("STK Push response:", response)


    return redirect('item_detail', item_reference=item_reference)


@login_required
def transaction_detail(request, transaction_reference):
    transaction = get_object_or_404(Transaction, transaction_reference=transaction_reference)

    if request.user != transaction.buyer and request.user != transaction.seller:
        return render(request, 'core/dashboard.html', {'message': "Access denied"})

    return render(request, 'core/transaction_detail.html', {'transaction': transaction})


@login_required
def buy_bulk_view(request, item_id):
    user = request.user
    # Check for essential profile fields
    required_fields = [
        user.national_id,
        user.phone_number,
        user.current_location,
        user.permanent_address,
        user.account_type,
        user.profile_picture,
        user.national_id_picture,
    ]

    if not all(required_fields):
        messages.warning(request, "Please complete your profile before posting an item.")
        return redirect('update_profile')
    item = get_object_or_404(Item, id=item_id)

    if not item.is_bulk or not item.bulk_price:
        messages.error(request, "This item is not available for bulk purchase.")
        return redirect('item_detail', item_id=item.id)

    if item.seller == request.user:
        messages.error(request, "You cannot buy your own item.")
        return redirect('item_detail', item_id=item.id)

    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity'))
            if quantity <= 0:
                raise ValueError
        except (TypeError, ValueError):
            messages.error(request, "Invalid quantity selected.")
            return redirect('buy_bulk', item_id=item.id)

        total_price = item.bulk_price * quantity
        delivery_address = request.POST.get('delivery_address')

        transaction_ref = str(uuid.uuid4()).replace('-', '')[:12]

        transaction = Transaction.objects.create(
            buyer=request.user,
            seller=item.seller,
            item=item,
            amount=total_price,
            status='pending',
            delivery_address=delivery_address,
            transaction_reference=transaction_ref,
            is_bulk=True,  # Add this if your Transaction model has it
            quantity=quantity  # Same here
        )

        phone = request.user.phone_number
        response = lipa_na_mpesa(
            phone_number=phone,
            amount=total_price,
            account_reference=transaction_ref,
            transaction_desc=f"Bulk Purchase {item.item_reference}"
        )

        if response.get("ResponseCode") == "0":
            messages.success(request, "Payment request sent. Check your phone.")
        else:
            messages.error(request, "Failed to initiate payment. Try again.")

        return redirect('transaction_detail', transaction.id)

    return render(request, 'core/buy_bulk.html', {'item': item})





from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from .models import SecureTransaction, MpesaPaymentLog
import logging
from django.core.mail import send_mail
mpesa_logger = logging.getLogger('mpesa')
@csrf_exempt
def mpesa_callback(request):
    if request.method != 'POST':
        return JsonResponse({"message": "Only POST requests are allowed"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid or empty JSON body"}, status=400)

    stk_callback = data.get("Body", {}).get("stkCallback", {})
    merchant_request_id = stk_callback.get("MerchantRequestID")
    checkout_request_id = stk_callback.get("CheckoutRequestID")
    result_code = stk_callback.get("ResultCode")
    result_desc = stk_callback.get("ResultDesc")

    amount = phone = mpesa_receipt = account_reference = None
    transaction_found = False

    if result_code == 0:
        callback_metadata = stk_callback.get("CallbackMetadata", {}).get("Item", [])
        metadata_dict = {item['Name']: item['Value'] for item in callback_metadata if 'Value' in item}

        amount = metadata_dict.get("Amount")
        mpesa_receipt = metadata_dict.get("MpesaReceiptNumber")
        phone = metadata_dict.get("PhoneNumber")
        account_reference = metadata_dict.get("AccountReference")

        # === 1. Match SecureTransaction ===
        try:
            st = SecureTransaction.objects.get(mpesa_reference=account_reference)
            st.transaction_status = 'paid'
            st.save()
            transaction_found = True
            mpesa_logger.info(f"[SECURE] Payment matched via reference {account_reference}")
        except SecureTransaction.DoesNotExist:
            pass

        # === 2. Match Transaction ===
        if not transaction_found:
            try:
                t = Transaction.objects.get(transaction_reference=account_reference)
                t.status = 'paid'                
                t.paid_at = timezone.now()
                t.save()
                transaction_found = True
                mpesa_logger.info(f"[INTERNAL] Payment matched via reference {account_reference}")
            except Transaction.DoesNotExist:
                pass

        # === 3. Notify for unmatched payments ===
        if not transaction_found and account_reference:
            try:
                    user = CustomUser.objects.get(national_id=account_reference)

                    start_date = timezone.now()
                    # expiry_date = start_date + timedelta(days=30)

                    sub, created = PremiumSubscription.objects.get_or_create(user=user)
                    sub.paid_date = start_date
                    # sub.expiry_date = expiry_date
                    sub.status = 'pending'  # Awaiting admin approval
                    sub.save()

                    # Email the admin team for manual review
                    message = (
                        f"PREMIUM APPLICATION RECEIVED:\n"
                        f"User: {user.get_full_name()} ({user.email})\n"
                        f"National ID: {account_reference}\n"
                        f"Phone: {phone}\n"
                        f"Amount: {amount}\n"
                        f"Receipt: {mpesa_receipt}"
                    )
                    send_mail(
                        subject=f"{account_reference} Premium Application via M-PESA",
                        message=message,
                        from_email=None,
                        recipient_list=['mpesa@safedeal.co.ke'],
                    )
                    mpesa_logger.info(message)

                    transaction_found = True
            except CustomUser.DoesNotExist:
                mpesa_logger.warning(f"National ID {account_reference} not found for premium activation.")
        else:
            message = (
                f"✅ M-PESA PAYMENT RECEIVED\n\n"
                f"Phone Number: {phone}\n"
                f"Amount: KES {amount}\n"
                f"Account Reference: {account_reference}\n"
                f"M-PESA Receipt: {mpesa_receipt}\n"
                f"Date: {now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            subject = f"✅ Payment Received | Ref: {account_reference}"
            send_mail(subject, message, from_email=None, recipient_list=['mpesa@safedeal.co.ke'])

    # === 4. Always log callback ===
    MpesaPaymentLog.objects.create(
        merchant_request_id=merchant_request_id,
        checkout_request_id=checkout_request_id,
        result_code=result_code,
        result_description=result_desc,
        amount=amount,
        phone=phone,
        mpesa_receipt=mpesa_receipt,
        transaction_reference=account_reference  # Add this field in your model if not present
    )

    return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})


from .models import MpesaB2CResult

@csrf_exempt
def mpesa_result_callback(request):
    data = json.loads(request.body)

    result = data.get('Result', {})

    # Extract useful fields
    result_code = result.get("ResultCode")
    result_desc = result.get("ResultDesc")
    conv_id = result.get("ConversationID")
    orig_conv_id = result.get("OriginatorConversationID")
    transaction_id = result.get("TransactionID")
    amount = 0
    phone_number = ""
    reference = ""

    # Pull transaction reference from ResultParameters if available
    parameters = result.get("ResultParameters", {}).get("ResultParameter", [])
    for param in parameters:
        if param["Key"] == "TransactionAmount":
            amount = float(param["Value"])
        if param["Key"] == "ReceiverPartyPublicName":
            phone_number = param["Value"].split("-")[0].strip()
        if param["Key"] == "InitiatedTime":
            pass
        if param["Key"] == "Occasion":
            reference = param["Value"]

    MpesaB2CResult.objects.create(
        transaction_reference=reference,
        phone_number=phone_number,
        amount=amount,
        result_type=data.get("ResultType", 0),
        result_code=result_code,
        result_desc=result_desc,
        originator_conversation_id=orig_conv_id,
        conversation_id=conv_id,
        transaction_id=transaction_id,
        raw_response=data
    )

    # Optionally update the transaction if needed
    if reference:
        try:
            transaction = Transaction.objects.get(transaction_reference=reference)
            if result_code == 0:
                transaction.is_funded = True
                transaction.funded_at = timezone.now()
                transaction.save()
        except Transaction.DoesNotExist:
            pass

    return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})

@csrf_exempt
def mpesa_timeout_callback(request):
    data = json.loads(request.body)

    conversation_id = data.get("ConversationID", "N/A")
    originator_id = data.get("OriginatorConversationID", "N/A")

    MpesaB2CResult.objects.create(
        transaction_reference="TIMEOUT",
        phone_number="N/A",
        amount=0,
        result_type=-1,
        result_code=-1,
        result_desc="Queue Timeout",
        originator_conversation_id=originator_id,
        conversation_id=conversation_id,
        transaction_id=None,
        raw_response=data
    )

    return JsonResponse({"ResultCode": 0, "ResultDesc": "Timeout logged"})



@login_required
def check_payment_status(request, transaction_id):
    try:
        transaction = Transaction.objects.get(id=transaction_id)

        if transaction.status == 'paid':
            return JsonResponse({'status': 'confirmed'})

        if transaction.checkout_request_id:
            result = query_stk_status(transaction.checkout_request_id)
            result_code = result.get("ResultCode")

            if result_code == "0":
                transaction.status = 'paid'
                transaction.paid_at = timezone.now()
                transaction.save()
                return JsonResponse({'status': 'confirmed'})
            elif result_code in ["1032", "1"]:
                return JsonResponse({'status': 'failed'})

        return JsonResponse({'status': 'pending'})

    except Transaction.DoesNotExist:
        return JsonResponse({'status': 'not_found'}, status=404)



# # Admin views for handling disputes


from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def admin_premium_subscriptions(request):
    pending_subs = PremiumSubscription.objects.filter(status='pending').select_related('user')

    return render(request, 'admin/pending_premium_subscriptions.html', {
        'pending_subs': pending_subs,
        'current_time': now(),
    })


def is_admin(user):
    return user.is_staff or user.is_superuser

@login_required
@user_passes_test(is_admin)
def manage_support_tickets(request):
    filter_status = request.GET.get('status', 'open')
    filter_type = request.GET.get('issue_type', '')

    tickets = SupportTicket.objects.all().order_by('-created_at')

    if filter_status == 'open':
        tickets = tickets.filter(is_resolved=False)
    elif filter_status == 'resolved':
        tickets = tickets.filter(is_resolved=True)

    if filter_type:
        tickets = tickets.filter(issue_type=filter_type)

    if request.method == 'POST':
        ticket_id = request.POST.get('ticket_id')
        action = request.POST.get('action')
        ticket = get_object_or_404(SupportTicket, id=ticket_id)

        if action == 'resolve':
            ticket.is_resolved = True
            ticket.save()
            messages.success(request, f"Ticket #{ticket.id} marked as resolved.")
            return redirect('manage_support_tickets')

    return render(request, 'admin/support_tickets.html', {
        'tickets': tickets,
        'filter_status': filter_status,
        'filter_type': filter_type,
        'issue_choices': SupportTicket.ISSUE_CHOICES,
    })

    
@staff_member_required
def approve_premium(request, sub_id):
    sub = get_object_or_404(PremiumSubscription, pk=sub_id, status='pending')
    start_date = timezone.now()
    sub.status = 'active'
    sub.user.is_premium = True    
    sub.premium_start_date = start_date
    sub.expiry_date = start_date + timedelta(days=30)
    sub.user.save()
    sub.save()
    messages.success(request, f"{sub.user.get_full_name()} has been approved as a premium user.")
    return redirect('admin_premium_subscriptions')


from django.core.paginator import Paginator
from itertools import chain
from operator import attrgetter

@staff_member_required
def all_transactions_admin(request):
    q = request.GET.get("q", "").strip()

    tx_qs = Transaction.objects.all().select_related("buyer", "seller", "item")
    secure_qs = SecureTransaction.objects.all().select_related("seller")

    if q:
        tx_qs = tx_qs.filter(transaction_reference__icontains=q)
        secure_qs = secure_qs.filter(mpesa_reference__icontains=q)

    # Mark type so we can distinguish in the template if needed
    for tx in tx_qs:
        tx.tx_type = 'regular'
    for tx in secure_qs:
        tx.tx_type = 'secure'

    # Combine and sort by creation date
    combined = sorted(
        chain(tx_qs, secure_qs),
        key=attrgetter('created_at'),
        reverse=True
    )

    # Manual pagination
    paginator = Paginator(combined, 30)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "admin/all_transactions.html", {
        "page_obj": page_obj,
        "search_query": q,
        "trans":tx_qs,
        "secure":secure_qs,
    })


@staff_member_required
def admin_close_dispute(request, transaction_id):
    dispute = get_object_or_404(TransactionDispute, transaction__id=transaction_id)
    transaction = dispute.transaction

    if request.method == 'POST':
        notes = request.POST.get('admin_notes')
        dispute.status = 'closed'
        dispute.admin_notes = notes
        dispute.save()

        if transaction.status == 'disputed':
            # Fetch the last status before 'disputed'
            previous_log = TransactionStatusLog.objects.filter(
                transaction=transaction
            ).exclude(new_status='disputed').order_by('-timestamp').first()

            restored_status = previous_log.new_status if previous_log else 'paid'

            log_transaction_status_change(
                transaction,
                new_status=restored_status,
                user=request.user,
                reason='Admin closed dispute, transaction restored to previous state'
            )
            send_custom_email(
                subject='Dispute Closed by Admin',
                template_name='emails/dispute_raised.html',
                context={
                    'buyer': transaction.buyer,
                    'item': transaction.item,
                    'reason': notes,
                },
                recipient_list=[transaction.buyer.email],
            )

        messages.success(request, "Dispute closed successfully.")
        return redirect('transaction_detail', transaction_id=transaction_id)

    return render(request, 'transactions/admin_close_dispute.html', {'dispute': dispute})
@login_required
def close_dispute(request, transaction_reference):
    dispute = get_object_or_404(TransactionDispute, transaction__transaction_reference=transaction_reference)
    transaction = dispute.transaction

    if request.method == 'POST':
        notes = f'This dispute was closed by {request.user}'
        dispute.status = 'closed'
        dispute.admin_notes = notes
        dispute.save()

        if transaction.status == 'disputed':
            previous_log = TransactionStatusLog.objects.filter(
                transaction=transaction
            ).exclude(new_status='disputed').order_by('-timestamp').first()

            restored_status = previous_log.new_status if previous_log else 'paid'

            log_transaction_status_change(
                transaction,
                new_status=restored_status,
                user=request.user,
                reason='User closed the dispute, transaction restored to previous state'
            )
            send_custom_email(
                subject='Dispute Closed',
                template_name='emails/dispute_closed.html',
                context={
                    'seller': transaction.seller,
                    'item': transaction.item,
                    'reason': notes,
                },
                recipient_list=[transaction.seller.email],
            )

        messages.success(request, "Dispute closed successfully.")
        return redirect('dashboard')

    return render(request, 'core/close_dispute.html', {'dispute': dispute})



from django.contrib.auth import get_user_model
User = get_user_model()
@staff_member_required
def admin_dashboard(request):
    user = request.user
    # Check for essential profile fields
    required_fields = [
        user.national_id,
        user.phone_number,
        user.current_location,
        user.permanent_address,
        user.account_type,
        user.profile_picture,
        user.national_id_picture,
    ]

    if not all(required_fields):
        messages.warning(request, "Please complete your profile before posting an item.")
        return redirect('update_profile')
    disputes = TransactionDispute.objects.all().order_by('-created_at')
    open_disputes = disputes.filter(status='open')
    closed_disputes = disputes.filter(status='closed')
    all_transactions = Transaction.objects.filter(status='disputed').order_by('-created_at') 
    unverified_users = User.objects.filter(is_verified=False).order_by('-date_joined')
    inactive_users = User.objects.filter(is_active=False).order_by('-date_joined')
    account_update_pending = User.objects.filter(is_active=True,
    ).filter(
        national_id__isnull=False,
        national_id_picture__isnull=False,
        profile_picture__isnull=False,
        is_verified=False  # You might need to add this field
    ).order_by('-date_joined')

    query = request.GET.get('q')
    if query:
        users = User.objects.filter(
            Q(username__icontains=query) | Q(email__icontains=query)
        ).order_by('-date_joined')
    else:
        users = User.objects.all().order_by('-date_joined')[:3]  # Limit for performance

    return render(request, 'admin/admin_dashboard.html', {
        'open_disputes': open_disputes,
        'closed_disputes': closed_disputes,
        'all_transactions': all_transactions,
        'users': account_update_pending,
        'unverified_users': unverified_users,
        'inactive_users': inactive_users,
    })
    
    
from django.contrib.auth.decorators import user_passes_test
@user_passes_test(lambda u: u.is_superuser)
def admin_toggle_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    if user == request.user:
        messages.error(request, "You cannot deactivate your own account.")
        return redirect('admindashboard')

    user.is_active = not user.is_active
    user.save()
    
    status = "activated" if user.is_active else "deactivated"
    messages.success(request, f"User '{user.username}' has been {status}.")
    return redirect('admindashboard')

@staff_member_required
def admin_user_list(request):
    query = request.GET.get('q')
    if query:
        users = User.objects.filter(
            Q(username__icontains=query) | Q(email__icontains=query)
        ).order_by('-date_joined')
    else:
        users = User.objects.all().order_by('-date_joined')
        
    return render(request, 'admin/admin_user_list.html', {'users': users})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if user == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect('admin_user_list')

    user.delete()
    messages.success(request, f"User '{user.username}' has been deleted.")
    return redirect('admin_user_list')

@user_passes_test(lambda u: u.is_staff)
def admin_verify_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_verified = True
    user.save()
    messages.success(request, f"{user.username}'s account has been verified successfully.")
    return redirect('admindashboard')

@user_passes_test(lambda u: u.is_staff)
def admin_user_verification_view(request, user_id):
    user = get_object_or_404(User, id=user_id)
    return render(request, 'admin/admin_user_verification.html', {'user_obj': user})

@staff_member_required
def promote_to_staff(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if not user.is_staff:
        user.is_staff = True
        user.save(update_fields=["is_staff"])
        messages.success(request, f"{user.get_full_name()} is now staff.")
    else:
        messages.info(request, f"{user.get_full_name()} is already staff.")
    return redirect("admin_user_list")
@staff_member_required
def demote_to_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if not user.is_staff:
        user.is_staff = False
        user.save(update_fields=["is_staff"])
        messages.success(request, f"{user.get_full_name()} is demoted to a regular user.")
    else:
        messages.info(request, f"{user.get_full_name()} is already a regular user.")
    return redirect("admin_user_list")

@staff_member_required
def all_items_view(request):
    items = Item.objects.all().order_by('-created_at')
    paginator = Paginator(items, 20)  # Show 20 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin/all_items.html', {'page_obj': page_obj, 'items': items})
