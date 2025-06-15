# subscriptions/views.py
import stripe
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from accounts.models import ClientSubscription
from django.utils import timezone

stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
def subscription_options(request):
    if hasattr(request.user, 'subscription') and request.user.subscription.active and not request.user.is_superuser:
        return redirect('dashboard')
    
    tiers = [
        {'id': 'basic', 'name': 'Basic', 'price': 29, 'features': ['1 Register', 'Basic Reports']},
        {'id': 'premium', 'name': 'Premium', 'price': 79, 'features': ['3 Registers', 'Advanced Reports']},
        {'id': 'enterprise', 'name': 'Enterprise', 'price': 199, 'features': ['Unlimited Registers', 'All Features']}
    ]
    return render(request, 'subscriptions/options.html', {'tiers': tiers})

@login_required
def create_checkout_session(request):
    tier = request.GET.get('tier', 'basic')
    
    # Price IDs from Stripe dashboard - REPLACE WITH YOUR ACTUAL IDs
    prices = {
        'basic': 'price_1RXiQXCMwGgIDHgwXHPTopGB',
        'premium': 'price_1RXiTwCMwGgIDHgwSxpHkdOm',
        'enterprise': 'price_1PJt5cKb9J9p9ZtXZ7v8X9Xw'
    }
    
    if tier not in prices:
        return HttpResponse("Invalid tier selected", status=400)
    
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': prices[tier],
                'quantity': 1,
            }],
            mode='subscription',
            success_url=request.build_absolute_uri('/subscriptions/success/'),
            cancel_url=request.build_absolute_uri('/subscriptions/'),
            metadata={'user_id': str(request.user.id), 'tier': tier},
            customer_email=request.user.email
        )
        return redirect(checkout_session.url)
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=400)

@login_required
def subscription_success(request):
    return render(request, 'subscriptions/success.html')

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    # Handle subscription events
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_checkout_session(session)
    
    return HttpResponse(status=200)

def handle_checkout_session(session):
    user_id = int(session['metadata']['user_id'])
    tier = session['metadata']['tier']
    customer_id = session.get('customer', '')
    subscription_id = session.get('subscription', '')
    
    # Create or update subscription
    ClientSubscription.objects.update_or_create(
        user_id=user_id,
        defaults={
            'tier': tier,
            'stripe_customer_id': customer_id,
            'stripe_subscription_id': subscription_id,
            'active': True,
            'expires_at': timezone.now() + timezone.timedelta(days=365)
        }
    )