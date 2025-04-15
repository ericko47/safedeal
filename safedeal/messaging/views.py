from django.shortcuts import render, redirect, get_object_or_404
from core.models import Item
from .models import Conversation, Message
from django.contrib.auth.decorators import login_required

@login_required
def start_conversation(request, item_id):
    item = get_object_or_404(Item, id=item_id)

    if item.seller == request.user:
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
