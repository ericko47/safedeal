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
        ('refurbished', 'Refurbished'),
    ]

    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    location = models.CharField(max_length=100, null=True, blank=True)  # Location of the item
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='used')
    is_available = models.BooleanField(default=True)
    is_personal = models.BooleanField(default=True)  # True = personal item, False = business listing
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class ItemImage(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='item_images/')
    
    def __str__(self):
        return f"Image for {self.item.title}"



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
    dispute_reason = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Transaction #{self.id} - {self.item.title} ({self.status})"
    
# Dispute model to handle disputes raised by buyers or sellers

class TransactionDispute(models.Model):
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    seller_response = models.TextField(blank=True, null=True)
    responded_at = models.DateTimeField(blank=True, null=True)
        # New fields
    status = models.CharField(max_length=20, choices=[('open', 'Open'), ('resolved', 'Resolved'), ('closed', 'Closed')], default='open')
    admin_notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Dispute for Transaction #{self.transaction.id}"



# All users database model 

class CustomUser(AbstractUser):
    # National ID with validation
    national_id = models.CharField(max_length=20, unique=True, null=True, blank=True, 
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
    is_verified = models.BooleanField(default=False)
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

# Transaction model to handle the transactions between buyers and sellers
# This model will include fields for the buyer, seller, item, amount, status, and other relevant details.
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class SecureTransaction(models.Model):
    TRANSACTION_STATUS = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('disputed', 'Disputed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='external_transactions')
    buyer_email = models.EmailField(help_text="Used to notify buyer about the transaction link.")
    buyer_phone = models.CharField(max_length=15,null=True, blank=True,validators=[RegexValidator(regex='^\+?1?\d{9,15}$', message='Invalid phone number')])
    buyer_name = models.CharField(max_length=100, null=True, blank=True)
    item_name = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_status = models.CharField(max_length=20, choices=TRANSACTION_STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    mpesa_reference = models.CharField(max_length=100, blank=True, null=True, unique=True)


    def get_secure_link(self):
        from django.urls import reverse
        return reverse('external_transaction_detail', kwargs={'transaction_id': str(self.id)})

    def __str__(self):
        return f"{self.item_name} ({self.seller.username}) - {self.transaction_status}"


#the transactions  that will store all necessary information for the transaction and escrow process.

from django.urls import reverse


class TransactionOut(models.Model):
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions_sold')
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions_bought')
    item = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('completed', 'Completed'), ('disputed', 'Disputed')], default='pending')
    escrow_status = models.CharField(max_length=20, choices=[('open', 'Open'), ('closed', 'Closed')], default='open')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    transaction_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    def get_transaction_link(self):
        return reverse('transaction_detail', kwargs={'transaction_code': self.transaction_code})

    def __str__(self):
        return f"Transaction {self.transaction_code} - {self.item}"

class MpesaPaymentLog(models.Model):
    merchant_request_id = models.CharField(max_length=100)
    checkout_request_id = models.CharField(max_length=100)
    result_code = models.IntegerField()
    result_description = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    mpesa_receipt = models.CharField(max_length=100, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.mpesa_receipt} - {self.amount}"


# Report model to handle item reports

User = get_user_model()

class ItemReport(models.Model):
    item = models.ForeignKey('Item', on_delete=models.CASCADE)
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    reviewed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('item', 'reported_by')  # Prevent multiple reports by same user
        
        
class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlists')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='wishlisted_by')
    added_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'item')  # prevent duplicate wishlisting

    def __str__(self):
        return f"{self.user} -> {self.item}"
