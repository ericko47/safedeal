from django.urls import path
from . import views

urlpatterns = [
    path('start/<str:item_reference>/', views.start_conversation, name='start_conversation'),
    path('conversation/<str:conversation_reference>/send/', views.send_message_ajax, name='send_message_ajax'),
    path('conversation/<str:conversation_reference>/fetch/', views.fetch_messages, name='fetch_messages'),
    path('conversation/<uuid:conversation_reference>/', views.conversation_detail, name='conversation_detail'),
    path('inbox/', views.inbox_view, name='inbox'),
    path('contact/', views.contact_us, name='contact_us'),
    path("conversation/<int:id>/", views.redirect_conversation_by_id)
    # path('conversation/<str:conversation_reference>/delete/', views.delete_conversation, name='delete_conversation'),
    # path('conversation/<str:conversation_reference>/delete_message/<int:message_id>/', views.delete_message, name='delete_message'),    

]
