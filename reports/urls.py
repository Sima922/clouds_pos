# urls.py
from django.urls import path
from .views import ReportsDashboardView, SalesReportView

app_name = 'reports'

urlpatterns = [
    path('', ReportsDashboardView.as_view(), name='dashboard'),
    path('sales-report/', SalesReportView.as_view(), name='sales-report'),
    
]