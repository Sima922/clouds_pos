# accounts/views.py

from django.views.generic import FormView
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages

from .forms import LoginForm, RegistrationForm
from .models import ClientSubscription, User

class CustomLoginView(FormView):
    """
    Renders the login form, authenticates via email, logs in any active user.
    """
    template_name = 'accounts/login.html'
    form_class = LoginForm
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        email = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(self.request, username=email, password=password)
        if user:
            login(self.request, user)
            return super().form_valid(form)
        form.add_error(None, "Invalid email or password")
        return self.form_invalid(form)


class CustomRegisterView(UserPassesTestMixin, FormView):
    """
    Lets superusers or active owners/admins register new users under their subscription.
    """
    template_name = 'accounts/register.html'
    form_class = RegistrationForm
    success_url = reverse_lazy('dashboard')

    def test_func(self):
        user = self.request.user
        # Superuser can register anyone
        if user.is_superuser:
            return True
        # Owners/admins can register under their active subscription
        if user.role in ['owner', 'admin']:
            sub = getattr(user, 'subscription', None) or getattr(user, 'owned_subscription', None)
            return bool(sub and sub.active)
        return False

    def handle_no_permission(self):
        messages.error(self.request, "You don’t have permission to register users.")
        return redirect('dashboard')

    def get_form_kwargs(self):
        """
        Pass the creator into the form so it can assign subscription & enforce limits.
        """
        kwargs = super().get_form_kwargs()
        kwargs['creator'] = self.request.user
        return kwargs

    def form_valid(self, form):
        creator = self.request.user

        # Determine subscription (superuser may bypass)
        subscription = None
        if not creator.is_superuser:
            subscription = getattr(creator, 'owned_subscription', None) or creator.subscription
            if not subscription or not subscription.active:
                messages.error(self.request, "You don't have an active subscription.")
                return redirect('dashboard')

            # Check plan’s user limit
            existing = subscription.members.exclude(pk=subscription.owner_id).count()
            if existing >= subscription.user_limit:
                messages.error(self.request, "User limit reached for your subscription plan.")
                return redirect('dashboard')

        # Create user but do NOT log them in
        new_user = form.save(commit=False)
        if subscription:
            new_user.subscription = subscription

        # If role=admin, mark staff so they see the admin site
        if new_user.role == 'admin':
            new_user.is_staff = True

        new_user.is_active = True
        new_user.save()

        messages.success(
            self.request,
            f"User {new_user.get_full_name()} ({new_user.role}) created successfully."
        )
        return super().form_valid(form)
