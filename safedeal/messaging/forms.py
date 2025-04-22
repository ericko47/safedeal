from django import forms
from .models import Message, ContactMessage

# class MessageForm(forms.ModelForm):
#     class Meta:
#         model = Message
#         fields = ['subject', 'body']
#         widgets = {
#             'subject': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
#             'body': forms.Textarea(attrs={'class': 'w-full p-2 border rounded', 'rows': 4}),
#         }




class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 5}),
        }
        labels = {
            'name': 'Your Name',
            'email': 'Your Email',
            'subject': 'Subject',
            'message': 'Message',
        }
        help_texts = {
            'name': 'Enter your full name.',
            'email': 'Enter a valid email address.',
            'subject': 'Enter the subject of your message.',
            'message': 'Type your message here.',
        }