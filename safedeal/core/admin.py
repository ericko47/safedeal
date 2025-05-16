from django.contrib import admin
from .utils import send_custom_email, log_transaction_status_change, calculate_fees, notify_funding
from .models import Transaction
from .views import fund_seller
from .models import SupportTicket
from .models import PremiumSubscription

@admin.register(PremiumSubscription)
class PremiumSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'paid_date', 'premium_start_date', 'expiry_date', 'status')
    list_filter = ('status',)
    search_fields = ('user__email', 'user__national_id', 'user__phone_number')
    actions = ['mark_as_active', 'mark_as_expired']

    def mark_as_active(self, request, queryset):
        for sub in queryset:
            sub.status = 'active'
            sub.user.is_premium = True
            sub.user.save()
            sub.save()
        self.message_user(request, "Selected subscriptions marked as active.")

    def mark_as_expired(self, request, queryset):
        for sub in queryset:
            sub.status = 'expired'
            sub.user.is_premium = False
            sub.user.save()
            sub.save()
        self.message_user(request, "Selected subscriptions marked as expired.")

    mark_as_active.short_description = "Mark selected as Active"
    mark_as_expired.short_description = "Mark selected as Expired"


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ['user', 'issue_type', 'reference', 'is_resolved', 'created_at']
    list_filter = ['is_resolved', 'issue_type', 'created_at']
    search_fields = ['user__username', 'reference', 'message']
    readonly_fields = ['attachment']
  
# Register your mod@admin.action(description='Fund selected sellers')
def fund_selected_transactions(modeladmin, request, queryset):
    for transaction in queryset.filter(is_funded=False):
        success, msg = fund_seller(transaction)
        if success:
            notify_funding(transaction)

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'buyer', 'seller', 'amount', 'is_funded')
    actions = [fund_selected_transactions]
  