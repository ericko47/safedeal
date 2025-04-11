from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.index, name='index'),    
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('browse/', views.browse_view, name='browse'),
    path('item/<int:item_id>/', views.item_detail, name='item_detail'),
    path('escrow/', views.escrow_view, name='escrow'),
    path('post_item/', views.post_item_view, name='post_item'),
    path('privacy/', views.privacy_view, name='privacy'),
    path('terms/', views.terms_view, name='terms'),
    path('logout/', views.logout_view, name='logout'), 
    path('profile/update/',views.update_profile, name='update_profile'),
    
    path('order/<int:item_id>/', views.place_order, name='place_order'),
    path('transaction/<int:transaction_id>/', views.transaction_detail, name='transaction_detail'),
    path('transaction/<int:transaction_id>/confirm/', views.confirm_delivery, name='confirm_delivery'),
    path('transaction/<int:transaction_id>/cancel/', views.cancel_transaction, name='cancel_transaction'),


]
