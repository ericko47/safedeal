from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator

class CustomUser(AbstractUser):
    # National ID with validation
    national_id = models.CharField(max_length=20, unique=True,
        validators=[RegexValidator(regex='^\d{3}-\d{2}-\d{4}$', message='Invalid National ID')]
    )
    # Profile picture
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    # National ID picture
    national_id_picture = models.ImageField(upload_to='national_ids/', null=True, blank=True)
    # Location (City/Town)
    current_location = models.CharField(max_length=100, null=True, blank=True)
    # Phone number with validation
    phone_number = models.CharField(max_length=15, unique=True,
        validators=[RegexValidator(regex='^\+?1?\d{9,15}$', message='Invalid phone number')]
    )
    # Date of birth
    date_of_birth = models.DateField(null=True, blank=True) 
    # Permanent address
    permanent_address = models.CharField(max_length=255, null=True, blank=True)   
    # Business name
    business_name = models.CharField(max_length=255, null=True, blank=True)
    # Business address
    business_address = models.CharField(max_length=255, null=True, blank=True)
    # Business license number
    business_license_number = models.CharField(max_length=50, null=True, blank=True) 
    # Account type: Buyer, Seller, or Both
    ACCOUNT_TYPE_CHOICES = [
        ('buyer', 'Buyer'),
        ('seller', 'Seller'),
        ('both', 'Both')
    ]
    account_type = models.CharField(
        max_length=6,
        choices=ACCOUNT_TYPE_CHOICES,
        default='buyer'
    )

    def __str__(self):
        return self.username
