# core/views_external.py
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from .models import SecureTransaction

def external_transaction_detail(request, transaction_id):
    """Public view (no login) so an outside buyer can track status."""
    tx = get_object_or_404(SecureTransaction, id=transaction_id)

    context = {
        "tx": tx,
        "timeline": [
            ("Paid"      , tx.transaction_status in ["paid","shipped","delivered","completed"]),
            ("Shipped"   , tx.transaction_status in ["shipped","delivered","completed"]),
            ("Delivered" , tx.transaction_status in ["delivered","completed"]),
            ("Completed" , tx.transaction_status == "completed"),
            ("Disputed"  , tx.transaction_status == "disputed"),
            ("Cancelled" , tx.transaction_status == "cancelled"),
        ],
    }
    return render(request, "core/external_tx_detail.html", context)
