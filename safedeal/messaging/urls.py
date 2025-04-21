from django.urls import path
from . import views

urlpatterns = [
    path('start/<int:item_id>/', views.start_conversation, name='start_conversation'),
    path('conversation/<int:conversation_id>/send/', views.send_message_ajax, name='send_message_ajax'),
    path('conversation/<int:conversation_id>/fetch/', views.fetch_messages, name='fetch_messages'),
    path('conversation/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('inbox/', views.inbox_view, name='inbox'),

]
