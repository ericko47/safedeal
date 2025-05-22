from django.contrib import admin
from .utils import send_custom_email, log_transaction_status_change, calculate_fees, notify_funding
from .models import Transaction
from .views import fund_seller
from .models import SupportTicket
from .models import PremiumSubscription, Item, ItemImage, CustomUser, MpesaB2CResult,  MpesaPaymentLog
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from django.utils.html import format_html

from .models import TransactionDispute
from django.contrib.auth.admin import UserAdmin


@admin.register(MpesaPaymentLog)
class MpesaPaymentLogAdmin(admin.ModelAdmin):
    list_display = [
        "mpesa_receipt", "amount", "phone", "result_code",
        "result_description", "timestamp", "transaction_reference"
    ]
    list_filter = ["result_code", "timestamp"]
    search_fields = [
        "mpesa_receipt", "phone", "transaction_reference",
        "merchant_request_id", "checkout_request_id"
    ]
    readonly_fields = [
        "merchant_request_id", "checkout_request_id", "result_code",
        "result_description", "amount", "phone", "mpesa_receipt",
        "timestamp", "transaction_reference"
    ]
    ordering = ["-timestamp"] 

@admin.register(MpesaB2CResult)
class MpesaB2CResultAdmin(admin.ModelAdmin):
    list_display = [
        "transaction_reference", "phone_number", "amount",
        "result_code", "result_desc", "completed_at", "transaction_id"
    ]
    list_filter = ["result_code", "completed_at"]
    search_fields = ["transaction_reference", "phone_number", "transaction_id", "conversation_id"]
    readonly_fields = [
        "transaction_reference", "phone_number", "amount",
        "result_type", "result_code", "result_desc",
        "originator_conversation_id", "conversation_id",
        "transaction_id", "completed_at", "raw_response"
    ]
    ordering = ["-completed_at"]

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = [
        "username", "email", "phone_number", "is_verified", "is_premium",
        "account_type", "current_location", "is_staff", "date_joined"
    ]
    list_filter = ["is_verified", "is_premium", "account_type", "is_staff"]
    search_fields = ["username", "email", "phone_number", "national_id"]
    ordering = ["-date_joined"]

    fieldsets = UserAdmin.fieldsets + (
        ("Verification & Profile", {
            "fields": (
                "phone_number", "national_id", "profile_picture", "national_id_picture", "is_verified"
            )
        }),
        ("Location & Identity", {
            "fields": (
                "current_location", "permanent_address", "date_of_birth"
            )
        }),
        ("Business Info", {
            "fields": (
                "business_name", "business_address", "business_license_number"
            )
        }),
        ("Account Type & Status", {
            "fields": (
                "account_type", "is_premium"
            )
        }),
    )

    readonly_fields = ["date_joined", "last_login"]

    def profile_picture_preview(self, obj):
        if obj.profile_picture:
            return format_html('<img src="{}" width="60" style="border-radius: 5px;" />', obj.profile_picture.url)
        return "-"
    profile_picture_preview.short_description = "Profile"



@admin.register(TransactionDispute)
class TransactionDisputeAdmin(admin.ModelAdmin):
    list_display = [
        "transaction", "reason", "status", "resolved", "created_at", "responded_at", "short_details"
    ]
    list_filter = ["status", "resolved", "reason", "created_at"]
    search_fields = [
        "transaction__transaction_reference", "transaction__item__title", "transaction__buyer__username", "transaction__seller__username"
    ]
    readonly_fields = ["created_at", "responded_at"]
    list_editable = ["resolved", "status"]
    ordering = ["-created_at"]

    def short_details(self, obj):
        return (obj.additional_details[:50] + '...') if obj.additional_details and len(obj.additional_details) > 50 else obj.additional_details
    short_details.short_description = "Details"

    actions = ["mark_as_resolved", "mark_as_unresolved"]
    def mark_as_resolved(self, request, queryset):
        for dispute in queryset:
            dispute.status = "resolved"
            dispute.resolved = True
            dispute.responded_at = timezone.now()
            dispute.save()
            self.message_user(request, f"Marked {dispute.transaction.transaction_reference} as resolved.")

class ItemImageInline(admin.TabularInline):
    model = ItemImage
    extra = 1  # Allow at least 1 image slot by default
    readonly_fields = ["image_preview"]

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 80px; height: auto;" />', obj.image.url)
        return "No image"
    image_preview.short_description = "Preview"
    
@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = [
        "title", "seller", "price", "is_available", "is_bulk",
        "category", "condition", "location", "created_at", "item_reference", "image_thumbnail"
    ]
    list_filter = [
        "category", "condition", "is_available", "is_bulk", "created_at"
    ]
    search_fields = [
        "title", "description", "seller__username", "item_reference", "location"
    ]
    readonly_fields = ["item_reference", "created_at", "updated_at"]
    ordering = ["-created_at"]
    inlines = [ItemImageInline]

    def image_thumbnail(self, obj):
        first_image = obj.images.first()
        if first_image and first_image.image:
            return format_html('<img src="{}" style="width: 60px; height: auto;" />', first_image.image.url)
        return "-"
    image_thumbnail.short_description = "Thumbnail"
    
    def mark_as_available(self, request, queryset):
        updated_count = queryset.update(is_available=True)
        self.message_user(request, f"Marked {updated_count} items as available.")


FINE_RATE = Decimal("0.02")
BUYER_GRACE_HOURS = 48
SELLER_DELAY_HOURS = 24
PLATFORM_RATE    = Decimal("0.05") 

@admin.action(description="🛠️ Apply fines, platform fee, and finalize transactions")
def apply_fines_and_finalize(modeladmin, request, queryset):
    now = timezone.now()
    fined = 0
    auto_delivered = 0
    updated = 0

    # Apply fine for delayed shippers (status = paid > 24h)
    late_shippers = Transaction.objects.filter(
        status="paid",
        paid_at__lte=now - timedelta(hours=SELLER_DELAY_HOURS),
        platform_fee=0
    )

    for tx in late_shippers:
        fine = tx.amount * FINE_RATE
        payout = tx.amount - fine
        tx.platform_fee = fine
        tx.seller_payout = payout
        tx.save(update_fields=["platform_fee", "seller_payout"])
        fined += 1

        send_custom_email(
            subject="Late-Shipment Fine Applied",
            template_name="emails/seller_fined.html",
            context={
                "transaction": tx,
                "fine": fine,
                "payout": payout,
                "year": now.year,
            },
            recipient_list=[tx.seller.email],
        )

    # Apply normal platform fee (status = shipped > 24h, no fine applied yet)
    regulars = Transaction.objects.filter(
        status="shipped",
        shipped_at__lte=now - timedelta(hours=SELLER_DELAY_HOURS),
        platform_fee=0
    )

    for tx in regulars:
        platform_fee = tx.amount * PLATFORM_RATE
        payout = tx.amount - platform_fee
        tx.platform_fee = platform_fee
        tx.seller_payout = payout
        tx.save(update_fields=["platform_fee", "seller_payout"])
        updated += 1

    # Auto-confirm delivery after 48h if buyer hasn't
    auto_confirm = Transaction.objects.filter(
        status="arrived",
        arrived_at__lte=now - timedelta(hours=BUYER_GRACE_HOURS)
    )

    for tx in auto_confirm:
        tx.status = "delivered"
        tx.save(update_fields=["status"])
        auto_delivered += 1

    modeladmin.message_user(
        request,
        f"✅ Done. {fined} fined, {updated} fees applied, {auto_delivered} auto-delivered."
    )

class TransactionDisputeInline(admin.StackedInline):
    model = TransactionDispute
    extra = 0
    can_delete = False
    readonly_fields = ["created_at", "responded_at"]
    fields = [
        "reason", "additional_details", "seller_response", "responded_at",
        "status", "resolved", "admin_notes"
    ]
    show_change_link = True  # Optional: allows clicking through to the dispute


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        "transaction_reference", "item", "status", "is_funded",
        "platform_fee", "seller_payout", "can_seller_request_funding", "hold_payout",
        "created_at", "actions_column", "amount", "seller", "buyer", "paid_at"
    ]
    list_filter = ["status", "is_funded", "hold_payout", "created_at"]

    search_fields = ["transaction_reference", "item__title", "buyer__username", "seller__username"]
    actions = [apply_fines_and_finalize]
    inlines = [TransactionDisputeInline]
    def actions_column(self, obj):
        request = self._current_request
        if request.user.is_superuser and obj.can_seller_request_funding():
            payout_url = reverse('admin:fund_transaction', args=[obj.pk])
            return format_html(f'<a class="button" href="{payout_url}">✅ Fund Seller</a>')
        return "-"
    actions_column.short_description = "Actions"

    # Store request to access in column methods
    def get_queryset(self, request):
        self._current_request = request
        return super().get_queryset(request)

    def fund_transaction(self, request, pk):
        from django.shortcuts import redirect, get_object_or_404
        from django.contrib import messages
        from mpesa.utils import initiate_b2c_payment

        if not request.user.is_superuser:
            messages.error(request, "You are not authorized to perform this action.")
            return redirect(reverse('admin:core_transaction_changelist'))

        tx = get_object_or_404(Transaction, pk=pk)

        if tx.can_seller_request_funding():
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


from django.contrib import admin
from .models import Item

