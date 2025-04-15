from django.urls import path
from . import views

urlpatterns = [
    path('start/<int:item_id>/', views.start_conversation, name='start_conversation'),
    path('conversation/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
]
