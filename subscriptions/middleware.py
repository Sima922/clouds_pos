from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings

class SubscriptionRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.exempt_paths = [
            reverse('admin:login'),
            reverse('template_login'),
            reverse('logout'),
            '/subscriptions/',
            '/static/',
            '/media/',
        ]

    def __call__(self, request):
        # Skip middleware for:
        # - Non-authenticated users
        # - Exempt paths
        # - When subscription not required
        if (not request.user.is_authenticated or 
           request.user.is_superuser or
 
            any(request.path.startswith(path) for path in self.exempt_paths) or
            not settings.SUBSCRIPTION_REQUIRED):
            return self.get_response(request)
        
        # Check if user has active subscription
        if not hasattr(request.user, 'subscription') or not request.user.subscription.active:
            return redirect('subscriptions:subscription_options')
        
        return self.get_response(request)