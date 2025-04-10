from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from .forms import CustomUserCreationForm, UserProfileForm, ItemForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from allauth.account.auth_backends import AuthenticationBackend
from django.contrib import messages
from .models import Item


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            user.backend = AuthenticationBackend
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
        if form.is_valid():
            item = form.save(commit=False)
            item.seller = request.user
            item.save()
            return redirect('item_detail', pk=item.pk)
    else:
        form = ItemForm()
    return render(request, 'core/post_item.html', {'form': form})

def item_detail(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    return render(request, 'core/viewitem.html', {'item': item})

def privacy_view(request): 
    return render(request, 'core/privacy.html')

def terms_view(request):
    return render(request, 'core/terms.html')