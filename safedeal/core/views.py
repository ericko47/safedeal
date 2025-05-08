from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from .forms import CustomUserCreationForm, UserProfileForm, ItemForm, DisputeForm, TransactionOutForm, ItemReportForm, ShippingForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from .models import Item , ItemImage, Transaction, TransactionDispute, TransactionOut, ItemReport, Wishlist, DisputeEvidence
import uuid
from django.http import HttpResponseForbidden
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Q
from mpesa.utils import lipa_na_mpesa,format_phone
from core.utils import send_custom_email



@login_required
def confirm_delivery(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)

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
                subject='Item Delivered Confirmation',
                template_name='emails/delivery_confirmed.html',
                context={
                    'seller': transaction.seller,
                    'item': transaction.item,
                },
                recipient_list=[transaction.seller.email],
            )   
        else:
            messages.warning(request, "This transaction is not in a 'shipped' state.")

    return redirect('transaction_detail', transaction_id=transaction.id)



@login_required
def cancel_transaction(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)

    if request.user != transaction.buyer:
        return HttpResponseForbidden("You are not authorized to cancel this transaction.")

    if request.method == 'POST':
        if transaction.status == 'pending':
            transaction.status = 'cancelled'
            transaction.save()
            messages.success(request, "Transaction has been cancelled.")
        else:
            messages.warning(request, "Only pending transactions can be cancelled.")
    return redirect('transaction_detail', transaction_id=transaction.id)


@login_required
def raise_dispute(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, buyer=request.user)

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
            # Update transaction status
            transaction.status = 'disputed'
            transaction.save()

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
                    else:
                        if not file.content_type.startswith('image/'):
                            messages.error(request, f"{file.name} is not a valid image.")
                            return render(request, 'core/raise_dispute.html', {'form': form, 'transaction': transaction})                    

                        DisputeEvidence.objects.create(dispute=dispute, file=file)
                
            send_custom_email(
                subject='Dispute Raised',
                template_name='emails/dispute_raised.html',
                context={
                    'buyer': transaction.buyer,
                    'item': transaction.item,
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
def ship_item(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, seller=request.user)

    if transaction.status != 'paid':
        messages.error(request, "Item cannot be shipped in its current state.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = ShippingForm(request.POST, request.FILES, instance=transaction)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.status = 'shipped'
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



def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            send_custom_email(
                subject='Welcome to SafeDeal!',
                template_name='emails/welcome_email.html',
                context={'user': user},
                recipient_list=[user.email],
            )  
            user.backend = 'allauth.account.auth_backends.AuthenticationBackend'                      
            login(request, user)            
            messages.success(request, 'Registration successful!')
            return redirect('dashboard')  # Redirect to dashboard after successful registration
    else:
        form = CustomUserCreationForm()

    return render(request, 'core/register.html', {'form': form})


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
    
    return render(request, 'core/dashboard.html', {
        'buyer_transactions': buyer_transactions,
        'seller_transactions': seller_transactions,
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
def delete_item_view(request, item_id):
    item = get_object_or_404(Item, id=item_id, seller=request.user)
    if request.method == 'POST':
        item.delete()
        messages.success(request, "Item deleted successfully.")
        return redirect('my_items')
    return render(request, 'core/confirm_delete.html', {'item': item})

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


def browse_view(request):
    category_filter = request.GET.get('category', '')
    query = request.GET.get('q', '')
    
    items = Item.objects.filter(is_available=True).order_by('-created_at')
    
    if category_filter:
        items = items.filter(category=category_filter)
    if query:
        items = items.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )
    categories = Item.CATEGORY_CHOICES
    
    return render(request, 'core/browse.html', {
        'items': items,
        'categories': categories,
        'selected_category': category_filter,
        'search_query': query,
    })
    
def search_items(request):
    query = request.GET.get('q')
    exact_matches = []
    keyword_matches = []

    if query:
        exact_matches = Item.objects.filter(item_reference__iexact=query)
        keyword_matches = Item.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        ).exclude(item_reference__iexact=query)

    context = {
        'query': query,
        'exact_matches': exact_matches,
        'keyword_matches': keyword_matches,
    }
    return render(request, 'core/search_results.html', context)

def escrow_view(request):
    return render(request, 'core/escrow.html')


@login_required
def post_item_view(request):
    
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

    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)
        files = request.FILES.getlist('images')

        if form.is_valid():
            item = form.save(commit=False)
            item.seller = request.user
            
            if item.is_bulk and not request.user.is_premium:
                messages.error(request, "Bulk listings are only available to Premium sellers. Please uncheck 'bulk' or upgrade your account.")
                return render(request, 'core/post-item.html', {'form': form})
            
            # Validate each file before saving
            for f in files:
                if f.size > 5 * 1024 * 1024:  # 5MB limit
                    messages.error(request, f"{f.name} is too large (max 5MB).")
                    return render(request, 'core/post-item.html', {'form': form})
                if not f.content_type.startswith('image/'):
                    messages.error(request, f"{f.name} is not a valid image.")
                    return render(request, 'core/post-item.html', {'form': form})

            item.save()

            for f in files:
                ItemImage.objects.create(item=item, image=f)

            messages.success(request, "Item posted successfully!")
            return redirect('post_item')
        else:
            messages.error(request, "There was an error with your form.")
    else:
        form = ItemForm()

    return render(request, 'core/post-item.html', {'form': form})


def item_detail(request, item_id):   
    item = get_object_or_404(Item, id=item_id)
    in_wishlist = False

    if request.user.is_authenticated:
        in_wishlist = Wishlist.objects.filter(user=request.user, item=item).exists()

    return render(request, 'core/viewitem.html', {
        'item': item,
        'in_wishlist': in_wishlist,
    })




@login_required
def report_item(request, item_id):
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
    item = get_object_or_404(Item, id=item_id)

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
            return redirect('item_detail', item_id=item.id)
    else:
        form = ItemReportForm()

    return render(request, 'core/report_item.html', {'form': form, 'item': item})

@login_required
def toggle_wishlist(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, item=item)

    if not created:
        wishlist_item.delete()

    return redirect('item_detail', item_id=item.id)

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


def transaction_out_detail(request, pk):
    transaction_out = get_object_or_404(TransactionOut, pk=pk)
    return render(request, 'core/transaction_out_detail.html', {'transaction_out': transaction_out})


def transaction_out_public_view(request, token):
    transaction = get_object_or_404(TransactionOut, transaction_token=token)
    return render(request, 'core/transaction_out_public.html', {
        'transaction': transaction,
    })
    
    

def external_transaction_detail(request, transaction_id):
    transaction = get_object_or_404(SecureTransaction, id=transaction_id)
    return render(request, 'core/external_transaction_detail.html', {
        'transaction': transaction
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
            transaction_desc=f"Payment for {transaction.item_reference}"
        )

        print("STK Push Response:", response)  # Optional debug

        # Optionally set status here
        transaction.transaction_status = 'pending'
        transaction.save()

        messages.success(request, 'Payment initiated. You will receive an M-PESA prompt shortly.')

        return render(request, 'core/payment_initiated.html', {'transaction': transaction})
    

from .forms import SecureTransactionForm
@login_required
def create_secure_transaction(request):
    if request.method == 'POST':
        form = SecureTransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.seller = request.user

            # If item_reference is provided, fill in item details
            item_ref = form.cleaned_data.get('item_reference')
            if item_ref:
                try:
                    item = Item.objects.get(item_reference=item_ref)
                    transaction.item_name = item.title
                    transaction.amount = item.price
                    transaction.description = item.description
                except Item.DoesNotExist:
                    form.add_error('item_reference', 'Invalid item reference.')

            transaction.save()
            return redirect('transaction_success', transaction_id=transaction.id)
    else:
        # Allow passing ?item_reference=xxx in GET
        initial_data = {}
        item_ref = request.GET.get('item_reference')
        if item_ref:
            initial_data['item_reference'] = item_ref
        form = SecureTransactionForm(initial=initial_data)
    
    return render(request, 'core/create_transaction.html', {'form': form})




@login_required
def place_order(request, item_id): 
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
    item = get_object_or_404(Item, id=item_id)
    if item.seller == request.user:
        messages.error(request, "You cannot buy your own item.")
        return redirect('item_detail', item_id=item.id)

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
            amount=item.price,
            account_reference=transaction_ref,
            transaction_desc=f"Purchase {item.item_reference}"
        )

        if response.get("ResponseCode") == "0":
            messages.success(request, "Payment request sent. Check your phone.")
        else:
            messages.error(request, "Failed to initiate payment. Try again.")

        return redirect('transaction_detail', transaction.id)

    return redirect('item_detail', item_id=item_id)


@login_required
def transaction_detail(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)

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
                t.save()
                transaction_found = True
                mpesa_logger.info(f"[INTERNAL] Payment matched via reference {account_reference}")
            except Transaction.DoesNotExist:
                pass

        # === 3. Notify for unmatched payments ===
        if not transaction_found:
            message = f"UNMATCHED PAYMENT:\nPhone: {phone}\nAmount: {amount}\nReference: {account_reference}\nReceipt: {mpesa_receipt}"
            send_mail(
                subject="Unmatched M-PESA Payment",
                message=message,
                from_email=None,
                recipient_list=['mpesa@safedeal.co.ke'],
            )
            mpesa_logger.warning(message)
        else:
            send_mail(
                subject="M-PESA Payment Received",
                message=f"Payment of KES {amount} received from {phone}.\nReceipt: {mpesa_receipt}",
                from_email=None,
                recipient_list=['mpesa@safedeal.co.ke'],
            )

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


import qrcode
import io
import base64
@login_required
def transaction_success(request, transaction_id):
    transaction = SecureTransaction.objects.get(id=transaction_id, seller=request.user)
    secure_link = request.build_absolute_uri(transaction.get_secure_link())

    # Generate QR code image in memory
    qr = qrcode.make(secure_link)
    buffer = io.BytesIO()
    qr.save(buffer, format='PNG')
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    return render(request, 'core/transaction_success.html', {
        'transaction': transaction,
        'secure_link': secure_link,
        'qr_code': qr_base64,
    })
    
def buyer_transaction_view(request, transaction_id):
    transaction = get_object_or_404(SecureTransaction, id=transaction_id)
    return render(request, 'core/buyer_transaction_view.html', {'transaction': transaction})



# # Admin views for handling disputes

from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def admin_close_dispute(request, transaction_id):
    dispute = get_object_or_404(TransactionDispute, transaction__id=transaction_id)

    if request.method == 'POST':
        notes = request.POST.get('admin_notes')
        dispute.status = 'closed'
        dispute.admin_notes = notes
        dispute.save()
        messages.success(request, "Dispute closed successfully.")
        return redirect('transaction_detail', transaction_id=transaction_id)

    return render(request, 'transactions/admin_close_dispute.html', {'dispute': dispute})




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
    all_transactions = Transaction.objects.all().order_by('-created_at') 
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





