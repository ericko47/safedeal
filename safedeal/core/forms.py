from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Item, Transaction, TransactionOut, TransactionDispute, Service
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = [
            'title', 'description', 'category', 'cv', 'evidence',
            'price', 'delivery_duration'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class CustomLoginForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise forms.ValidationError(
                _("Your account is not verified yet. Please check your email and click the activation link we sent you."),
                code='inactive',
            )



class CustomUserCreationForm(UserCreationForm):
    phone_number = forms.CharField(
        max_length=15,
        help_text="Enter your M-PESA registered phone number."
    )
    email = forms.EmailField(
        help_text="Enter an active email address you can access (for account activation)."
    )

    class Meta:
        model = CustomUser
        fields = (
            'first_name',
            'last_name',
            'username',
            'email',
            'phone_number',
            'password1',
            'password2'
        )
# For users to update their profile after registration
from django import forms

class UserProfileForm(forms.ModelForm):
    date_of_birth = forms.DateField(
        input_formats=[
            '%d/%m/%Y',   # 25/06/2025
            '%Y-%m-%d',   # 2025-06-25 (ISO, for compatibility)
        ],
        widget=forms.TextInput(attrs={
            'placeholder': 'DD/MM/YYYY',
            'class': 'form-control'
        })
    )

    national_id_picture = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={
            "accept": "image/*",
            "capture": "environment"
        }),
        required=False
    )
    profile_picture = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={
            "accept": "image/*",
            "capture": "environment"
        }),
        required=False
    )

    class Meta:
        model = CustomUser
        fields = [
            'national_id',
            'profile_picture',
            'national_id_picture',
            'current_location',
            'phone_number',
            'date_of_birth',
            'permanent_address',
            'business_name',
            'business_address',
            'business_license_number',
            'account_type'
        ]





class ItemForm(forms.ModelForm):
    # Additional field for multiple images
    # images = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}), required=False)
    class Meta:
        model = Item
        fields = ['title', 'description','location', 'price', 'category', 'condition', 'is_bulk', 'bulk_price']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

   
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if not title:
            raise forms.ValidationError('This field is required.')
        if len(title) < 3:
            raise forms.ValidationError('Title must be at least 3 characters long.')
        return title

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if not description:
            raise forms.ValidationError('This field is required.')
        if len(description) < 20:
            raise forms.ValidationError('Description must be at least 20 characters long.')
        return description
    
    def clean_location(self):
        location = self.cleaned_data.get('location')
        if len(location) < 3:
            raise forms.ValidationError('Location must be at least 3 characters long be name of a place or town or City.')
        return location

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price <= 0:
            raise forms.ValidationError('Price must be a positive number.')
        return price
    
    
    def clean_category(self):
        category = self.cleaned_data.get('category')
        if not category:
            raise forms.ValidationError('This field is required.')
        return category

    def clean_condition(self):
        condition = self.cleaned_data.get('condition')
        if not condition:
            raise forms.ValidationError('This field is required.')
        return condition
    
    def clean_bulk_price(self):
        bulk_price = self.cleaned_data.get('bulk_price')
        is_bulk = self.cleaned_data.get('is_bulk')
        
        if is_bulk and not bulk_price:
            raise forms.ValidationError('Bulk price is required if bulk purchase is enabled.')
        return bulk_price



DISPUTE_REASONS = [
    ('item_not_received', 'Item not received'),
    ('item_not_as_described', 'Item not as described'),
    ('delayed_delivery', 'Delayed delivery'),
    ('damaged_item', 'Item arrived damaged'),
    ('wrong_item', 'Wrong item received'),
    ('other', 'Other'),
    ]

class DisputeForm(forms.Form):
    reason = forms.ChoiceField(
        label="Dispute Reason",
        choices=DISPUTE_REASONS,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )
    additional_details = forms.CharField(
        label="Additional Details (Optional)",
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Explain the issue further if needed...'}),
        max_length=1000,
        required=False
    )
    def clean(self):
        cleaned_data = super().clean()
        reason = cleaned_data.get("reason")
        additional_details = cleaned_data.get("additional_details")

        if reason == 'other' and not additional_details:
            self.add_error('additional_details', "Please provide more details for 'Other' reason.")

        return cleaned_data

    
class ShippingForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['shipping_evidence', 'delivery_mode', 'delivery_agent']
        widgets = {
            'delivery_mode': forms.Select(attrs={'class': 'form-select'}),
            'delivery_agent': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        mode = cleaned_data.get('delivery_mode')
        agent = cleaned_data.get('delivery_agent')

        if mode == 'agent' and not agent:
            raise forms.ValidationError("Please select a delivery agent.")
        return cleaned_data

    
    
    
    
from django.contrib.auth import get_user_model


class TransactionOutForm(forms.ModelForm):
    class Meta:
        model = TransactionOut
        fields = ['external_seller', 'item', 'amount', 'description', 'transaction_status']  # removed transaction_reference

    external_seller = forms.CharField(max_length=255, label="Seller Name")
    item = forms.CharField(max_length=255, label="Item Name")
    amount = forms.DecimalField(max_digits=10, decimal_places=2, label="Transaction Amount")
    description = forms.CharField(widget=forms.Textarea, label="Description", required=False)
    transaction_status = forms.ChoiceField(
        choices=[('pending', 'Pending'), ('completed', 'Completed')],
        label="Transaction Status"
    )
    
from .models import SecureTransaction

from .models import SecureTransaction

class SecureTransactionForm(forms.ModelForm):
    class Meta:
        model = SecureTransaction
        exclude = ['seller', 'transaction_status', 'created_at', 'updated_at','shipped_at', 'mpesa_reference', 'description', 'amount','platform_fee', 'seller_payout', 'funded_at','is_funded','hold_payout','item_name','checkout_request_id']
 
        labels = {
            'item_reference': 'Item ID',
        }
        help_texts = {
            'item_reference': 'Paste the SafeDeal Item ID from your listing (e.g., SDI-123456)',
        }

    def clean_buyer_phone(self):
        phone = self.cleaned_data.get('buyer_phone')
        if not phone.startswith('+') and not phone.isdigit():
            raise forms.ValidationError("Phone number must be valid and include country code.")
        return phone




class ItemReportForm(forms.Form):
    reason = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), label="Reason for Reporting")

# forms.py

from .models import DeliveryOrganization, DeliveryAgent

class DeliveryOrganizationForm(forms.ModelForm):
    class Meta:
        model = DeliveryOrganization
        fields = [
            'name', 'registration_number','contact_person', 'contact_email',
            'contact_phone', 'headquarters_location', 'logo'
        ]

class DeliveryAgentForm(forms.ModelForm):
    registering_as = forms.ChoiceField(
        choices=[('individual', 'Individual'), ('organization', 'Organization')],
        widget=forms.RadioSelect,
        label="Registering As"
    )

    class Meta:
        model = DeliveryAgent
        fields = [
            'vehicle_type', 'vehicle_plate_number', 'license_document', 'police_clearance_certificate', 'region_of_operation','mpesa_phone_number',
            'license_number', 'license_document'
        ]
