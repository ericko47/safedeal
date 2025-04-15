from django import forms
from .models import Message

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['subject', 'body']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'body': forms.Textarea(attrs={'class': 'w-full p-2 border rounded', 'rows': 4}),
        }
