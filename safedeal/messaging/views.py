from django.shortcuts import render, redirect, get_object_or_404
from core.models import Item
from .models import Conversation, Message
from django.contrib.auth.decorators import login_required

from django.contrib import messages


from .forms import ContactForm

@login_required
def start_conversation(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    if not item.is_available:
        messages.error(request, "This item is no longer available.")
        return redirect('item_detail', item_id=item.id)
    if not item.seller.is_active:
        messages.error(request, "The seller is no longer active.")
        return redirect('item_detail', item_id=item.id)
    if item.seller == request.user:
        # Prevent sellers from starting a conversation with themselves  
        messages.error(request, "You cannot start a conversation with yourself.")
        return redirect('item_detail', item_id=item.id)

    conversation, created = Conversation.objects.get_or_create(
        buyer=request.user,
        seller=item.seller,
        item=item
    )

    return redirect('conversation_detail', conversation_id=conversation.id)

@login_required
def conversation_detail(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)

    if request.method == 'POST':
        content = request.POST.get('message')
        if content:
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content
            )

    messages = conversation.messages.order_by('timestamp')
    return render(request, 'messaging/conversation_detail.html', {'conversation': conversation, 'messages': messages})

@login_required
def inbox_view(request):
    threads = Conversation.objects.filter(
        buyer=request.user
    ) | Conversation.objects.filter(
        seller=request.user
    )
    threads = threads.distinct().order_by('-created_at')

    return render(request, 'messaging/inbox.html', {'threads': threads})


from django.http import JsonResponse

@login_required
def send_message_ajax(request, conversation_id):
    if request.method == 'POST':
        conversation = get_object_or_404(Conversation, id=conversation_id)
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
def fetch_messages(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)
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
