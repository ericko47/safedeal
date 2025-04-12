from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from .forms import CustomUserCreationForm, UserProfileForm, ItemForm, DisputeForm, SellerResponseForm, TransactionOutForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from .models import Item , ItemImage, Transaction, TransactionDispute, TransactionOut
import uuid
from django.http import HttpResponseForbidden
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Q
from mpesa.utils import lipa_na_mpesa



@login_required
def place_order(request, item_id):
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
            transaction_desc=f"Purchase {item.title}"
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
def confirm_delivery(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)

    if request.user != transaction.buyer:
        return HttpResponseForbidden("You are not authorized to confirm this delivery.")

    if request.method == 'POST':
        if transaction.status == 'shipped':
            transaction.status = 'delivered'
            transaction.save()
            messages.success(request, "Delivery confirmed. Funds will now be released to the seller.")
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
def confirm_delivery(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, buyer=request.user)
    if request.method == 'POST' and transaction.status == 'shipped':
        transaction.status = 'delivered'
        transaction.save()
        messages.success(request, "Delivery confirmed successfully.")
    return redirect('dashboard')


@login_required
def cancel_transaction(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, buyer=request.user)
    if request.method == 'POST' and transaction.status == 'pending':
        transaction.status = 'cancelled'
        transaction.save()
        messages.warning(request, "Transaction cancelled.")
    return redirect('dashboard')


@login_required
def raise_dispute(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, buyer=request.user)
    if request.method == 'POST' and transaction.status in ['paid', 'shipped']:
        transaction.status = 'disputed'
        transaction.save()
        messages.error(request, "Dispute raised. Our team will review it.")
    return redirect('dashboard')


@login_required
def respond_to_dispute(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, seller=request.user)
    dispute = get_object_or_404(TransactionDispute, transaction=transaction)

    if request.method == 'POST':
        form = SellerResponseForm(request.POST, instance=dispute)
        if form.is_valid():
            dispute = form.save(commit=False)
            dispute.responded_at = timezone.now()
            dispute.save()
            messages.success(request, 'Your response has been submitted.')
            return redirect('transaction_detail', transaction_id=transaction.id)
    else:
        form = SellerResponseForm(instance=dispute)

    return render(request, 'core/respond_to_dispute.html', {'form': form, 'dispute': dispute, 'transaction': transaction})



def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
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

def login_view(request):
    next_url = request.GET.get('next', '')
    if next_url:
        messages.info(request, "Please log in to continue.")
   
    return render(request, 'core/login.html')


@login_required
def dashboard_view(request):
    transactions = Transaction.objects.filter(buyer=request.user).order_by('-created_at')
    return render(request, 'core/dashboard.html', {'transactions': transactions})

@login_required
def profile_view(request):
    return render(request, 'core/profile.html')

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
    

def escrow_view(request):
    return render(request, 'core/escrow.html')


@login_required

def post_item_view(request):
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)
        files = request.FILES.getlist('images')

        if form.is_valid():
            item = form.save(commit=False)
            item.seller = request.user

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
    return render(request, 'core/viewitem.html', {'item': item})


@login_required
def user_transactions_view(request):
    transactions = Transaction.objects.filter(buyer=request.user).order_by('-created_at')
    return render(request, 'core/my_transactions.html', {'transactions': transactions})



@login_required
def dispute_transaction(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, buyer=request.user)

    if transaction.status not in ['paid', 'shipped']:
        messages.warning(request, "You can only dispute transactions that are paid or shipped.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = DisputeForm(request.POST)
        if form.is_valid():
            transaction.status = 'disputed'
            transaction.dispute_reason = form.cleaned_data['dispute_reason']
            transaction.save()
            messages.success(request, "Dispute submitted successfully.")
            return redirect('transaction_detail', transaction_id=transaction.id)
    else:
        form = DisputeForm()

    return render(request, 'core/dispute_transaction.html', {
        'form': form,
        'transaction': transaction
    })


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
    return render(request, 'core/transaction_out_public.html', {'transaction': transaction})





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

@staff_member_required
def admin_dashboard(request):
    disputes = TransactionDispute.objects.all().order_by('-created_at')
    open_disputes = disputes.filter(status='open')
    closed_disputes = disputes.filter(status='closed')
    all_transactions = Transaction.objects.all().order_by('-created_at')

    return render(request, 'admin/admin_dashboard.html', {
        'open_disputes': open_disputes,
        'closed_disputes': closed_disputes,
        'all_transactions': all_transactions,
    })