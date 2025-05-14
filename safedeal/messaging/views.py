from django.shortcuts import render, redirect, get_object_or_404
from core.models import Item, Transaction
from .models import Conversation, Message
from django.contrib.auth.decorators import login_required

from django.contrib import messages
from django.db.models import Q

from .forms import ContactForm


@login_required
def start_conversation(request, item_reference):
    item = get_object_or_404(Item, item_reference=item_reference)

    if not item.is_available and not Transaction.objects.filter(item=item, status='disputed').exists():
        messages.error(request, "This item is no longer available.")
        return redirect('item_detail', item_reference=item.item_reference)

    if not item.seller.is_active:
        messages.error(request, "The seller is no longer active.")
        return redirect('item_detail', item_reference=item.item_reference)

    # Prevent user from messaging themselves on their own item
    if item.seller == request.user:
        # Try to find the latest transaction involving this item
        try:
            transaction = Transaction.objects.filter(item=item).latest('created_at')
            buyer = transaction.buyer
            seller = request.user
        except Transaction.DoesNotExist:
            messages.error(request, "No buyer found to contact.")
            return redirect('item_detail', item_reference=item.item_reference)
    else:
        buyer = request.user
        seller = item.seller

    # Ensure consistent roles (buyer/seller)
    conversation, created = Conversation.objects.get_or_create(
        buyer=buyer,
        seller=seller,
        item=item
    )

    return redirect('conversation_detail', conversation_reference=conversation.conversation_reference)


@login_required
def conversation_detail(request, conversation_reference):
    conversation = get_object_or_404(
    Conversation,
    Q(conversation_reference=conversation_reference) & (Q(buyer=request.user) | Q(seller=request.user))
    )
    # Mark all unread messages *not* sent by current user as read
    conversation.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)

    if request.method == 'POST':
        content = request.POST.get('message')
        if content:
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content
            )

    messages = conversation.messages.order_by('timestamp')
    return render(request, 'messaging/conversation_detail.html', {
        'conversation': conversation,
        'messages': messages
    })

def redirect_conversation_by_id(request, id):
    conversation = get_object_or_404(Conversation, id=id)
    return redirect('conversation_detail', conversation_reference=conversation.conversation_reference)


@login_required
def inbox_view(request):
    threads = Conversation.objects.filter(
        buyer=request.user
    ) | Conversation.objects.filter(
        seller=request.user
    )
    threads = threads.distinct().order_by('-created_at')

    # Check for unread messages not sent by current user
    has_unread_messages = Message.objects.filter(
        conversation__in=threads,
        is_read=False
    ).exclude(sender=request.user).exists()

    return render(request, 'messaging/inbox.html', {
        'threads': threads,
        'has_unread_messages': has_unread_messages
    })


from django.http import JsonResponse

@login_required
def send_message_ajax(request, conversation_reference):
    if request.method == 'POST':
        conversation = get_object_or_404(Conversation, conversation_reference=conversation_reference)
        content = request.POST.get('message')
        if content:
            msg = Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content
            )
            return JsonResponse({
                'sender': msg.sender.username,
                'content': msg.content,
                'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            })
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def fetch_messages(request, conversation_reference):
    conversation = get_object_or_404(Conversation, conversation_reference=conversation_reference)
    messages = conversation.messages.order_by('timestamp')
    messages_data = [{
        'sender': msg.sender.username,
        'content': msg.content,
        'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    } for msg in messages]

    return JsonResponse({'messages': messages_data})


def contact_us(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your message has been sent. We'll get back to you soon.")
            return redirect('contact_us')
    else:
        form = ContactForm()
    
    return render(request, 'messaging/contact_us.html', {'form': form})
