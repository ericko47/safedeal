from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LoginView
from .forms import CustomLoginForm

urlpatterns = [
    path('', views.index, name='index'),    
    # path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('login/', LoginView.as_view(template_name='core/login.html',authentication_form=CustomLoginForm), name='login'),
    
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('transactions/purchases/', views.all_purchases_view, name='all_purchases'),
    path('transactions/sales/', views.all_sales_view, name='all_sales'),
    path('profile/', views.profile_view, name='profile'),
    path('browse/', views.browse_view, name='browse'),    
    path("i/<str:item_reference>/", views.item_detail, name="item_shortlink"),
    path('item/<str:item_reference>/', views.item_detail, name='item_detail'),
    path('escrow/', views.escrow_view, name='escrow'),
    path('post_item/', views.post_item_view, name='post_item'),
    path('item/<str:item_reference>/report/', views.report_item, name='report_item'),
    path('wishlist/', views.view_wishlist, name='view_wishlist'),
    path('wishlist/toggle/<str:item_reference>/', views.toggle_wishlist, name='toggle_wishlist'),
    path('privacy/', views.privacy_view, name='privacy'),
    path('terms/', views.terms_view, name='terms'),
    path('about/', views.about_view, name='about'),
    path('how_it_works/', views.how_it_works, name='how_it_works'),
    path('faq/', views.faq, name='faq'),
    path('search/', views.search_items, name='search_items'),
    path('logout/', views.logout_view, name='logout'), 
    path('support/', views.support, name='support'), 
    path('upgrade/', views.upgrade_to_premium, name='upgrade_to_premium'),
    path('profile/update/',views.update_profile, name='update_profile'),
    path('admin_dashboard/', views.admin_dashboard, name='admindashboard'),    
    path('my-items/', views.my_items_view, name='my_items'),    
    path('delete-item/<str:item_reference>/', views.delete_item_view, name='delete_item'),
    path('toggle-user/<int:user_id>/', views.admin_toggle_user, name='admin_toggle_user'),
    path('admin_user_list/', views.admin_user_list, name='admin_user_list'),    
    path('admin_delete_user/delete/<int:user_id>/', views.admin_delete_user, name='admin_delete_user'),
    path('admin_verify_user/<int:user_id>/', views.admin_verify_user, name='admin_verify_user'),
    path('admin_user_verification_view/<int:user_id>/', views.admin_user_verification_view, name='admin_user_verification'),
    path('promote_to_staff/<int:user_id>/', views.promote_to_staff, name='promote_to_staff'),
    path('demote_to_user/<int:user_id>/', views.demote_to_user, name='demote_to_user'),


    path('order/<str:item_reference>/', views.place_order, name='place_order'),
    path('buy-bulk/<int:item_id>/', views.buy_bulk_view, name='buy_bulk'),
    path('leave_rating/<str:transaction_reference>/', views.leave_rating, name='leave_rating'),
    path('transaction/<str:transaction_reference>/', views.transaction_detail, name='transaction_detail'),
    path('transaction/<str:transaction_reference>/confirm/', views.confirm_delivery, name='confirm_delivery'),
    path('transaction/<str:transaction_reference>/cancel/', views.cancel_transaction, name='cancel_transaction'),
    path('transaction/<str:transaction_reference>/confirm/', views.confirm_delivery, name='confirm_delivery'),
    path('transaction/<str:transaction_reference>/dispute/', views.raise_dispute, name='raise_dispute'),
    path('transaction/<str:transaction_reference>/ship/', views.ship_item, name='ship_item'),
    path('secure-tx/<str:mpesa_reference>/ship/', views.ship_item_by_mpesa, name='ship_item_mpesa'),
    path('transactions/<int:transaction_id>/close-dispute/', views.admin_close_dispute, name='admin_close_dispute'),
    path('transactions/<str:transaction_reference>/close-dispute/', views.close_dispute, name='close_dispute'),
    path('transactions/<str:transaction_reference>/request_refund/', views.request_refund, name='request_refund'),
    path('transactions/<str:transaction_reference>/request_funding/', views.request_funding, name='request_funding'),
    path('transactions/<str:transaction_reference>/mark-arrived/', views.mark_arrived, name='mark_arrived'),
    path('transactions/<str:mpesa_reference>/mark_securelyarrived/', views.mark_securearrived, name='mark_securearrived'),
    path('transactions/<str:mpesa_reference>/mark_securedelivered/', views.mark_securedelivered, name='mark_securedelivered'),


    path("transactions/", views.all_transactions_admin, name="all_transactions_admin"),
    path('admin/premium-subscriptions/<int:sub_id>/approve/', views.approve_premium, name='approve_premium'),
    path('premium-subscriptions/', views.admin_premium_subscriptions, name='admin_premium_subscriptions'),
    path('reported_items/', views.reported_items_view, name='reported_items'),
    path('manage_support_tickets/', views.manage_support_tickets, name='manage_support_tickets'),
    path("fundable-transactions/", views.fundable_transactions, name="fundable_transactions"),
    path("held-transactions/", views.held_transactions, name="held_transactions"),
    path("fund_seller_external/<str:transaction_id>/", views.fund_seller_external, name="fund_seller_external"),
    path("fund-seller/<int:transaction_id>/", views.fund_seller, name="fund_seller"),
    path("toggle-hold/<int:transaction_id>/", views.toggle_hold_payout, name="toggle_hold_payout"),
    path("toggle-hold2/<str:transaction_id>/", views.toggle_hold_payout2, name="toggle_hold_payout2"),
    path("hold/<int:transaction_id>/", views.hold_payout, name="hold_payout"),
    path("hold2/<str:transaction_id>/", views.hold_payout2, name="hold_payout2"),

    
    path('register_delivery_agent/', views.register_delivery_agent, name='register_delivery_agent'),
    path('generate_transaction_out/', views.generate_transaction_out, name='generate_transaction_out'),
    path('my_delivery_jobs/', views.my_delivery_jobs, name='my_delivery_jobs'),
    path('verify-agents/', views.verify_agents_view, name='verify_agents'),

    path('create-transaction/', views.create_secure_transaction, name='create_secure_transaction'),
    path('transaction-success/<uuid:transaction_id>/', views.transaction_success, name='transaction_success'),    
    path('secure-transaction/<uuid:transaction_id>/', views.external_transaction_detail, name='external_transaction_detail'),
    path('secure-transaction/<uuid:transaction_id>/confirm/', views.initiate_payment, name='initiate_payment'),
    
    path('mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),
    path('mpesa/b2c/result/', views.mpesa_result_callback, name='mpesa_b2c_result_callback'),
    path('mpesa/b2c/timeout/', views.mpesa_timeout_callback, name='mpesa_b2c_timeout_callback'),
    path('check-payment-status/<int:transaction_id>/', views.check_payment_status, name='check_payment_status'),

    path('activate/<uidb64>/<token>/', views.activate_account, name='activate_account'),
    path('password-reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
   
    path('change-password/', auth_views.PasswordChangeView.as_view(template_name='accounts/change_password.html'), name='change_password'),
    path('change-password/done/', auth_views.PasswordChangeDoneView.as_view(template_name='accounts/change_password_done.html'), name='password_change_done'),
   
    path("secure-tx/<str:mpesa_reference>/ship/", views.ship_item_by_mpesa, name="ship_item_mpesa"),
    path('items/', views.all_items_view, name='all_items'),
    
    
    path('services/', views.service_list, name='service_list'),
    path('services/new/', views.create_service, name='create_service'),
    path('services/<uuid:uid>/', views.service_detail, name='service_detail'),
    path('services/hire/<uuid:uuid>/', views.hire_service, name='hire_service'),
    path('services/<uuid:uuid>/arrived/', views.mark_service_arrived, name='mark_service_arrived'),
    path('services/<uuid:uuid>/delivered/', views.confirm_service_delivery, name='confirm_service_delivery'),

]
