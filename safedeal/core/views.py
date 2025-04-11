from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from .forms import CustomUserCreationForm, UserProfileForm, ItemForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from allauth.account.auth_backends import AuthenticationBackend
from django.contrib import messages
from .models import Item , ItemImage, Transaction
import uuid
from django.http import HttpResponseForbidden
from .models import Transaction



@login_required
def place_order(request, item_id):
    item = get_object_or_404(Item, id=item_id)

    if item.seller == request.user:
        # Prevent users from buying their own item
        return render(request, 'core/error.html', {'message': "You cannot purchase your own item."})

    transaction = Transaction.objects.create(
        buyer=request.user,
        seller=item.seller,
        item=item,
        amount=item.price,
        delivery_address=request.user.permanent_address or "To be provided",
        transaction_reference=str(uuid.uuid4()),
        status='pending'
    )

    return redirect('transaction_detail', transaction_id=transaction.id)


@login_required
def transaction_detail(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)

    if request.user != transaction.buyer and request.user != transaction.seller:
        return render(request, 'core/error.html', {'message': "Access denied"})

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

# def login_view(request):
#     return render(request, 'core/login.html')

@login_required
def dashboard_view(request):
    return render(request, 'core/dashboard.html')

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
    items = Item.objects.filter(is_available=True).order_by('-created_at')
    return render(request, 'core/browse.html', {'items': items})

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
            item.save()

            for f in files:
                ItemImage.objects.create(item=item, image=f)

            return redirect('dashboard')  # or wherever
    else:
        form = ItemForm()
        return render(request, 'core/post-item.html', {'form': form})

def item_detail(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    return render(request, 'core/viewitem.html', {'item': item})

def privacy_view(request): 
    return render(request, 'core/privacy.html')

def terms_view(request):
    return render(request, 'core/terms.html')