from django.urls import path
from . import views

urlpatterns = [                         

    path('api/mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),

    path('stk-push/', views.initiate_stk_push, name='initiate_stk_push'),
]