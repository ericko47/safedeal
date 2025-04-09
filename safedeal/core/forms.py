from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

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
        fields = ('username', 'email','phone_number', 'password1', 'password2')

# For users to update their profile after registration
# This form can be used to update the user's profile after registration.
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['national_id', 'profile_picture', 'national_id_picture', 'current_location', 'phone_number', 'date_of_birth', 'permanent_address', 'business_name', 'business_address', 'business_license_number', 'account_type']
