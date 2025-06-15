from django.urls import path
from . import views

app_name = 'subscriptions'

urlpatterns = [
    path('', views.subscription_options, name='subscription_options'),
    path('create-checkout-session/', views.create_checkout_session, name='create_checkout_session'),
    path('success/', views.subscription_success, name='subscription_success'),
    path('webhook/', views.stripe_webhook, name='stripe_webhook'),
]