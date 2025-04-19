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
    path('my-items/', views.my_items_view, name='my_items'),    
    path('delete-item/<int:item_id>/', views.delete_item_view, name='delete_item'),
    

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
    
    path('create-transaction/', views.create_secure_transaction, name='create_secure_transaction'),
    path('transaction-success/<uuid:transaction_id>/', views.transaction_success, name='transaction_success'),
    path('secure/<uuid:transaction_id>/', views.buyer_transaction_view, name='buyer_transaction_view'),
    path('transaction/<uuid:token>/', views.transaction_out_public_view, name='transaction_out_public_view'),
    path('secure-transaction/<uuid:transaction_id>/', views.external_transaction_detail, name='external_transaction_detail'),

    path('secure-transaction/<uuid:transaction_id>/confirm/', views.initiate_payment, name='initiate_payment'),
    
    path('mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),
  


    # Password reset URLs
    path('password-reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
   


    path('change-password/', auth_views.PasswordChangeView.as_view(template_name='accounts/change_password.html'), name='change_password'),
    path('change-password/done/', auth_views.PasswordChangeDoneView.as_view(template_name='accounts/change_password_done.html'), name='password_change_done'),


]
