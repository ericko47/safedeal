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
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),

    path('order/<int:item_id>/', views.place_order, name='place_order'),
    path('transaction/<int:transaction_id>/', views.transaction_detail, name='transaction_detail'),
    path('transaction/<int:transaction_id>/confirm/', views.confirm_delivery, name='confirm_delivery'),
    path('transaction/<int:transaction_id>/cancel/', views.cancel_transaction, name='cancel_transaction'),
    path('transaction/<int:transaction_id>/confirm/', views.confirm_delivery, name='confirm_delivery'),
    path('transaction/<int:transaction_id>/dispute/', views.raise_dispute, name='raise_dispute'),
    path('transaction/<int:transaction_id>/dispute/', views.dispute_transaction, name='dispute_transaction'),
    path('transactions/<int:transaction_id>/close-dispute/', views.admin_close_dispute, name='admin_close_dispute'),
    
    path('generate_transaction_out/', views.generate_transaction_out, name='generate_transaction_out'),
    path('transaction_out/<int:pk>/', views.transaction_out_detail, name='transaction_out_detail'),
    path('t/<uuid:token>/', views.transaction_out_public_view, name='transaction_out_public'),


]
