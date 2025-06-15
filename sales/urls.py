from django.urls import path
from .views import (
    POSView, 
    OrdersView,
    OrderListCreate,
    OrderDetail,
    generate_receipt
)

app_name = 'sales'  # This is important

urlpatterns = [
    # UI Views
    path('', POSView.as_view(), name='pos-ui'),
    path('orders/', OrdersView.as_view(), name='orders-ui'),
    
    # API Endpoints
    path('api/orders/', OrderListCreate.as_view(), name='order-list'),
    path('api/orders/<int:pk>/', OrderDetail.as_view(), name='order-detail'),
    path('api/orders/<int:order_id>/receipt/', generate_receipt, name='order-receipt'),
    path('orders/<int:pk>/receipt/', generate_receipt, name='order-receipt-pk')
]
