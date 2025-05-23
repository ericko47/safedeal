from django.db import models
from django.conf import settings
import core.models 
import uuid

class Conversation(models.Model):
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='buyer_conversations', on_delete=models.CASCADE)
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='seller_conversations', on_delete=models.CASCADE)
    item = models.ForeignKey('core.Item', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    conversation_reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    def participants(self):
        return [self.buyer, self.seller]

    def __str__(self):
        return f"{self.buyer} - {self.seller} ({self.item.title})"

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)    
    def __str__(self):
        return f"Message from {self.sender.username} at {self.timestamp}"    
    

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=150)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.subject}"
