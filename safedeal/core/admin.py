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

from django.utils.html import format_html
from django.urls import reverse


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        "transaction_reference", "item", "status", "is_funded",
        "platform_fee", "seller_payout", "can_seller_request_funding", "hold_payout",
        "created_at", "actions_column"
    ]
    list_filter = ["status", "is_funded", "hold_payout", "created_at"]

    search_fields = ["transaction_reference", "item__title", "buyer__username", "seller__username"]

    def actions_column(self, obj):
        if obj.needs_funding():
            payout_url = reverse('admin:fund_transaction', args=[obj.pk])
            return format_html(f'<a class="button" href="{payout_url}">✅ Fund Seller</a>')
        return "-"
    actions_column.short_description = "Actions"

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('fund/<int:pk>/', self.admin_site.admin_view(self.fund_transaction), name='fund_transaction'),
        ]
        return custom_urls + urls

    def fund_transaction(self, request, pk):
        from django.shortcuts import redirect, get_object_or_404
        from django.contrib import messages
        from core.utils import initiate_b2c_payment  # You must have this logic already

        tx = get_object_or_404(Transaction, pk=pk)

        if tx.needs_funding():
            response = initiate_b2c_payment(
                phone_number=tx.seller.phone_number,
                amount=tx.seller_payout,
                transaction_id=tx.id
            )
            if response.get("ResultCode") == 0:
                tx.is_funded = True
                tx.funded_at = timezone.now()
                tx.save(update_fields=["is_funded", "funded_at"])
                messages.success(request, f"Seller funded successfully for TX {tx.transaction_reference}.")
            else:
                messages.error(request, f"Failed to fund seller: {response.get('ResultDesc')}")
        else:
            messages.warning(request, "Transaction is not eligible for funding.")

        return redirect(reverse('admin:core_transaction_changelist'))

  