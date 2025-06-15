# core/urls.py

from django.urls import path, include, reverse_lazy
from django.contrib import admin
from django.views.generic import RedirectView, TemplateView
from django.contrib.auth.views import LogoutView
from accounts.views import CustomLoginView, CustomRegisterView

urlpatterns = [
    # Root → login
    path('', RedirectView.as_view(url=reverse_lazy('template_login')), name='root'),

    # Auth UI
    path('login/', CustomLoginView.as_view(), name='template_login'),
    path('logout/', LogoutView.as_view(next_page='template_login'), name='logout'),
    path('register/', CustomRegisterView.as_view(), name='template_register'),

    # Dashboard
    path('dashboard/', TemplateView.as_view(template_name='dashboard/index.html'), name='dashboard'),

    # App modules
    path('pos/', include('sales.urls')),
    path('products/', include('products.urls')),
    path('reports/', include('reports.urls')),
    path('subscriptions/', include('subscriptions.urls')),

    # API
    path('api/auth/', include('accounts.api.urls')),
    path('api/sales/', include('sales.api_urls')),

    # Admin
    path('admin/', admin.site.urls),
]
