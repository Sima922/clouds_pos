import logging
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse, JsonResponse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.utils.html import escape
from rest_framework.authentication import SessionAuthentication
from decimal import Decimal
from django.core.exceptions import FieldError
from django.conf import settings

from .models import Order, OrderItem
from .serializers import OrderSerializer
from products.models import Product
from customers.models import Customer
from core.utils import currency

logger = logging.getLogger(__name__)

def get_user_subscription(user):
    """
    Return the ClientSubscription for this user (member or owner),
    or None if they have no subscription.
    """
    sub = getattr(user, 'subscription', None)
    if sub:
        return sub
    return getattr(user, 'owned_subscription', None)

# ──────────────────────────────────────────────────────────────────────────────
# REST API: Orders
# ──────────────────────────────────────────────────────────────────────────────

class OrderListCreate(generics.ListCreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        sub = get_user_subscription(self.request.user)
        if not sub:
            return Order.objects.none()
        return Order.objects.filter(user__subscription=sub)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        sub = get_user_subscription(request.user)
        if not sub:
            return Response({"detail": "No active subscription."},
                            status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save(user=request.user, subscription=sub)

        order.status = 'completed'
        order.calculate_total()
        order.calculate_change()
        order.update_inventory()
        order.save(update_fields=['status', 'total', 'change_given'])

        logger.info(f"Order #{order.id} completed for subscription={sub}.")
        return Response(self.get_serializer(order).data,
                        status=status.HTTP_201_CREATED)


class OrderDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        sub = get_user_subscription(self.request.user)
        if not sub:
            return Order.objects.none()
        return Order.objects.filter(user__subscription=sub)


# ──────────────────────────────────────────────────────────────────────────────
# Browser views: POS & Orders
# ──────────────────────────────────────────────────────────────────────────────

class POSView(LoginRequiredMixin, TemplateView):
    template_name = 'sales/pos.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sub = get_user_subscription(self.request.user)
        
        # Add currency settings to context
        context['CURRENCY_SYMBOL'] = getattr(settings, 'CURRENCY_SYMBOL', 'P')
        context['CURRENCY'] = getattr(settings, 'CURRENCY', 'BWP')

        if sub:
            # Products scoped to subscription
            context['products'] = Product.objects.filter(
                subscription=sub,
                is_active=True
            ).order_by('name')

            # Customers: only filter by subscription if field exists
            try:
                context['customers'] = Customer.objects.filter(
                    subscription=sub
                ).order_by('name')
            except (FieldError, AttributeError):
                context['customers'] = Customer.objects.all()
        else:
            context['products'] = Product.objects.none()
            context['customers'] = Customer.objects.none()

        context['default_tax'] = 8
        context['default_discount'] = 0
        return context


class OrdersView(LoginRequiredMixin, TemplateView):
    template_name = 'sales/orders.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sub = get_user_subscription(self.request.user)
        
        # Add currency settings to context
        context['CURRENCY_SYMBOL'] = getattr(settings, 'CURRENCY_SYMBOL', 'P')
        context['CURRENCY'] = getattr(settings, 'CURRENCY', 'BWP')

        if sub:
            context['orders'] = Order.objects.filter(
                user__subscription=sub
            ).prefetch_related('items')[:50]
        else:
            context['orders'] = Order.objects.none()

        return context


def currency_settings(request):                                                                                                         
    """
    Add currency settings to template context with safe defaults.
    """
    return {
        'CURRENCY_SYMBOL': getattr(settings, 'CURRENCY_SYMBOL', 'P'),
        'CURRENCY': getattr(settings, 'CURRENCY', 'BWP'),
        'THOUSAND_SEPARATOR': getattr(settings, 'THOUSAND_SEPARATOR', True),
        'DECIMAL_PLACES': getattr(settings, 'DECIMAL_PLACES', 2),
    }

def format_currency(amount):
    """Format currency with proper symbol, thousand separator and decimal places."""
    currency_symbol = getattr(settings, 'CURRENCY_SYMBOL', 'P')
    use_thousand_separator = getattr(settings, 'THOUSAND_SEPARATOR', True)
    decimal_places = getattr(settings, 'DECIMAL_PLACES', 2)
    
    # Format the number with decimal places
    formatted_amount = f"{float(amount):.{decimal_places}f}"
    
    # Add thousand separator if enabled
    if use_thousand_separator:
        parts = formatted_amount.split('.')
        parts[0] = f"{int(parts[0]):,}"
        formatted_amount = '.'.join(parts)
    
    return f"{currency_symbol}{formatted_amount}"

@login_required
def generate_receipt(request, order_id):
    """Generate receipt for an order with better error handling and business name header."""
    try:
        # 1) Try fetching order without subscription filter to check existence
        try:
            order_obj = Order.objects.select_related('customer', 'user').get(id=order_id)
        except Order.DoesNotExist:
            logger.error(f"Order {order_id} does not exist")
            return JsonResponse({"detail": f"Order {order_id} not found."}, status=404)

        # 2) Check subscription access for requesting user
        sub_req = get_user_subscription(request.user)
        if not sub_req:
            logger.error(f"User {request.user} has no subscription")
            return JsonResponse({"detail": "No active subscription."}, status=403)

        # Determine subscription of the order owner
        sub_order_owner = get_user_subscription(order_obj.user)
        if sub_order_owner != sub_req:
            logger.error(
                f"User {request.user} (sub: {sub_req}) cannot access order {order_id} "
                f"(belongs to sub: {sub_order_owner})"
            )
            return JsonResponse({"detail": "Access denied."}, status=403)

        # 3) Gather items and compute totals
        items_qs = order_obj.items.select_related('product').all()
        subtotal = sum(item.total_price for item in items_qs)
        discount_amount = subtotal * (order_obj.discount / Decimal('100'))
        tax_amount = (subtotal - discount_amount) * (order_obj.tax_rate / Decimal('100'))

        # 4) Determine business name from subscription
        if sub_order_owner and getattr(sub_order_owner, 'business_name', None):
            business_name = sub_order_owner.business_name
        else:
            business_name = "CloudPOS"

        # Format all currency values properly
        context = {
            'business_name': business_name,
            'order': order_obj,
            'items': items_qs,
            'subtotal': format_currency(subtotal),
            'discount_amount': format_currency(discount_amount),
            'tax_amount': format_currency(tax_amount),
            'total': format_currency(order_obj.total),
            'amount_paid': format_currency(order_obj.amount_paid) if order_obj.amount_paid else None,
            'change_given': format_currency(order_obj.change_given) if order_obj.change_given else None,
            'formatted_date': order_obj.created_at.strftime('%Y-%m-%d %H:%M'),
            'customer_name': getattr(order_obj.customer, 'name', 'Walk-in'),
            'cashier_name': request.user.get_full_name() or request.user.email,
            'currency_symbol': getattr(settings, 'CURRENCY_SYMBOL', 'P'),
            # Format individual item prices for template
            'formatted_items': [
                {
                    'product': item.product,
                    'quantity': item.quantity,
                    'price': format_currency(item.price),
                    'total_price': format_currency(item.total_price),
                    'name': item.product.name
                }
                for item in items_qs
            ]
        }

        # 5) Render HTML if requested
        if request.GET.get('format') == 'html':
            try:
                html = render_to_string('sales/receipt.html', context)
                return HttpResponse(html, content_type='text/html')
            except Exception as e:
                logger.error(f"Error rendering receipt template: {e}")
                return JsonResponse({
                    'detail': 'Error rendering receipt template.',
                    'error': str(e)
                }, status=500)

        # 6) JSON fallback
        return JsonResponse({
            'order_id': order_obj.id,
            'total': float(order_obj.total),
            'items_count': items_qs.count(),
        })

    except Exception as e:
        logger.error(f"Error generating receipt for order {order_id}: {e}")
        return JsonResponse({"detail": f"Error generating receipt: {str(e)}"}, status=500)


# ──────────────────────────────────────────────────────────────────────────────
# Debug/Test Endpoints
# ──────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def test_auth(request):
    return Response({
        'authenticated': True,
        'user': request.user.email,
        'subscription': str(get_user_subscription(request.user))
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def debug_orders(request):
    sub = get_user_subscription(request.user)
    if not sub:
        return Response({'orders': []})
    orders = Order.objects.filter(user__subscription=sub) \
                          .values('id', 'created_at', 'total')
    return Response({
        'subscription': str(sub),
        'orders': list(orders)
    })
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def simple_receipt_test(request, order_id):
    return JsonResponse({'message': f'Got order_id: {order_id}', 'user': str(request.user)})