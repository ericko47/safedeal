from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Item, Transaction, ItemImage

class CustomUserCreationForm(UserCreationForm):
    # national_id = forms.CharField(max_length=20)
    phone_number = forms.CharField(max_length=15)
    # date_of_birth = forms.DateField(required=False)
    # permanent_address = forms.CharField(max_length=255, required=False)
    # business_name = forms.CharField(max_length=255, required=False)
    # business_address = forms.CharField(max_length=255, required=False)
    # business_license_number = forms.CharField(max_length=50, required=False)
    # profile_picture = forms.ImageField(required=False)
    # national_id_picture = forms.ImageField(required=False)
    # current_location = forms.CharField(max_length=100, required=False)
    # account_type = forms.ChoiceField(choices=CustomUser.ACCOUNT_TYPE_CHOICES)

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

  
