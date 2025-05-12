from django.contrib import admin
from .utils import send_custom_email, log_transaction_status_change, calculate_fees, notify_funding
from .models import Transaction
from .views import fund_seller


# Register your mod@admin.action(description='Fund selected sellers')
def fund_selected_transactions(modeladmin, request, queryset):
    for transaction in queryset.filter(is_funded=False):
        success, msg = fund_seller(transaction)
        if success:
            notify_funding(transaction)

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'buyer', 'seller', 'amount', 'is_funded')
    actions = [fund_selected_transactions]
  