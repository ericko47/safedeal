from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.conf import settings
from django.utils import timezone



# Item model to handle the items listed for sale
# This model will include fields for the seller, title, description, price, category, condition, image, and other relevant details.
class Item(models.Model):
    CATEGORY_CHOICES = [
        ('electronics', 'Electronics'),
        ('furniture', 'Furniture'),
        ('clothing', 'Clothing'),
        ('vehicles', 'Vehicles'),
        ('services', 'Services'),
        ('other', 'Other'),
    ]

    CONDITION_CHOICES = [
        ('new', 'New'),
        ('used', 'Used'),
    ]

    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='items')
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    location = models.CharField(max_length=100, null=True, blank=True)  # Location of the item
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='used')
    image = models.ImageField(upload_to='item_images/', null=True, blank=True)
    is_available = models.BooleanField(default=True)
    is_personal = models.BooleanField(default=True)  # True = personal item, False = business listing
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title





# Transaction model to handle the transactions between buyers and sellers
# This model will include fields for the buyer, seller, item, amount, status, and other relevant details.
class Transaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('disputed', 'Disputed'),
    ]

    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='purchases',
        on_delete=models.CASCADE
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='sales',
        on_delete=models.CASCADE
    )
    item = models.ForeignKey('core.Item', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    delivery_address = models.CharField(max_length=255)
    delivery_method = models.CharField(max_length=100, blank=True, null=True)
    payment_method = models.CharField(max_length=100, blank=True, null=True)
    transaction_reference = models.CharField(max_length=100, unique=True)
    proof_of_delivery = models.ImageField(upload_to='deliveries/', null=True, blank=True)

    def __str__(self):
        return f"Transaction #{self.id} - {self.item.title} ({self.status})"



# All users database model 

class CustomUser(AbstractUser):
    # National ID with validation
    national_id = models.CharField(max_length=20, unique=True,
        validators=[RegexValidator(regex='^\d{6,10}$', message='Invalid National ID')]
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
        ('both', 'Both Buyer and Seller')
    ]
    account_type = models.CharField(
        max_length=6,
        choices=ACCOUNT_TYPE_CHOICES,
        default='both'
    )

    def __str__(self):
        return self.username
