from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Item, Transaction, TransactionOut, TransactionDispute


from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _

class CustomLoginForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise forms.ValidationError(
                _("Your account has been deactivated due to a pending issue. Please contact support."),
                code='inactive',
            )



class CustomUserCreationForm(UserCreationForm):
    phone_number = forms.CharField(max_length=15)

    class Meta:
        model = CustomUser
        fields = ('first_name','last_name','username', 'email','phone_number', 'password1', 'password2')

# For users to update their profile after registration
# This form can be used to update the user's profile after registration.
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['national_id', 'profile_picture', 'national_id_picture', 'current_location', 'phone_number', 'date_of_birth', 'permanent_address', 'business_name', 'business_address', 'business_license_number', 'account_type']






class ItemForm(forms.ModelForm):
    # Additional field for multiple images
    # images = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}), required=False)
    class Meta:
        model = Item
        fields = ['title', 'description','location', 'price', 'category', 'condition']
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

  
class DisputeForm(forms.Form):
    dispute_reason = forms.CharField(
        label="Reason for Dispute",
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe the issue...'}),
        max_length=1000,
        required=True
        
    )
    def clean_dispute_reason(self):
        dispute_reason = self.cleaned_data.get('dispute_reason')
        if not dispute_reason:
            raise forms.ValidationError('This field is required.')
        return dispute_reason
# DisputeResponseForm is used by the seller to respond to a dispute raised by the buyer.
    
class SellerResponseForm(forms.ModelForm):
    class Meta:
        model = TransactionDispute
        fields = ['seller_response']
        widgets = {
            'seller_response': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter your response to the dispute...'}),
        }
    def clean_seller_response(self):
        seller_response = self.cleaned_data.get('seller_response')
        if not seller_response:
            raise forms.ValidationError('This field is required.')
        return seller_response  
    
    
    
    
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

class SecureTransactionForm(forms.ModelForm):
    class Meta:
        model = SecureTransaction
        exclude = ['seller', 'transaction_status', 'created_at', 'updated_at', 'mpesa_reference']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_buyer_phone(self):
        phone = self.cleaned_data.get('buyer_phone')
        if not phone.startswith('+') and not phone.isdigit():
            raise forms.ValidationError("Phone number must be valid and include country code.")
        return phone




class ItemReportForm(forms.Form):
    reason = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), label="Reason for Reporting")
