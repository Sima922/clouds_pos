from django.urls import path
from .views import (
    OrderListCreate,
    OrderDetail,
    generate_receipt,
    test_auth,
    debug_orders,
    simple_receipt_test,
)

app_name = 'sales_api'

urlpatterns = [
    path('orders/', OrderListCreate.as_view(), name='order-list'),
    path('orders/<int:pk>/', OrderDetail.as_view(), name='order-detail'),
    path('orders/<int:order_id>/receipt/', generate_receipt, name='order-receipt'),

    # Utility endpoints
    path('test-auth/', test_auth, name='test-auth'),
    path('debug-orders/', debug_orders, name='debug-orders'),
    path('simple-test/<int:order_id>/', simple_receipt_test, name='simple-test'),
]

