# reports/models.py

from django.db import models, transaction
from django.utils import timezone
from django.db.models import Sum, F
from decimal import Decimal

from sales.models import Order
from products.models import Product
from accounts.models import ClientSubscription

class SalesReport(models.Model):
    subscription = models.ForeignKey(
        ClientSubscription,
        on_delete=models.CASCADE,
        related_name='sales_reports', null=True, blank=True
    )
    report_date = models.DateField(auto_now_add=True)
    start_date = models.DateField()
    end_date = models.DateField()
    total_sales = models.DecimalField(max_digits=12, decimal_places=2)
    total_orders = models.IntegerField()
    total_items_sold = models.IntegerField()
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    exported = models.BooleanField(default=False)
    export_format = models.CharField(max_length=10, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['subscription', 'report_date']),
            models.Index(fields=['subscription', 'start_date', 'end_date']),
        ]

    @classmethod
    def generate_daily_report(cls, subscription):
        """
        Generate (and save) a daily report for 'today' for the given subscription.
        """
        today = timezone.now().date()
        # Filter orders by subscription and completed today
        orders = Order.objects.filter(
            created_at__date=today,
            status='completed',
            subscription=subscription
        )

        total_sales = orders.aggregate(total=Sum('total'))['total'] or Decimal('0')
        total_orders = orders.count()
        total_items = orders.aggregate(items=Sum('items__quantity'))['items'] or 0
        avg_order = (total_sales / total_orders) if total_orders > 0 else Decimal('0')

        with transaction.atomic():
            # Example: if you track days_in_stock on Product, you'd update only for this subscription’s products:
            # Product.objects.filter(subscription=subscription).update(days_in_stock=F('days_in_stock') + 1)
            return cls.objects.create(
                subscription=subscription,
                start_date=today,
                end_date=today,
                total_sales=total_sales,
                total_orders=total_orders,
                total_items_sold=total_items,
                average_order_value=avg_order
            )

    @classmethod
    def generate_range_report(cls, subscription, start_date, end_date):
        """
        Generate a report for arbitrary date range for this subscription.
        """
        orders = Order.objects.filter(
            created_at__date__range=(start_date, end_date),
            status='completed',
            subscription=subscription
        )
        total_sales = orders.aggregate(total=Sum('total'))['total'] or Decimal('0')
        total_orders = orders.count()
        total_items = orders.aggregate(items=Sum('items__quantity'))['items'] or 0
        avg_order = (total_sales / total_orders) if total_orders > 0 else Decimal('0')

        return cls.objects.create(
            subscription=subscription,
            start_date=start_date,
            end_date=end_date,
            total_sales=total_sales,
            total_orders=total_orders,
            total_items_sold=total_items,
            average_order_value=avg_order
        )


class InventoryAgingReport(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='aging_reports'
    )
    date_received = models.DateField()
    quantity = models.IntegerField()
    days_in_stock = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_received']
        indexes = [
            models.Index(fields=['days_in_stock']),
            models.Index(fields=['product', 'date_received']),
        ]

    @classmethod
    def update_aging_for_subscription(cls, subscription):
        """
        Increment days_in_stock only for aging records whose products belong to this subscription.
        """
        # Fetch products in this subscription
        qs = cls.objects.filter(product__subscription=subscription)
        qs.update(days_in_stock=F('days_in_stock') + 1)

    @classmethod
    def update_aging_all(cls):
        """
        Increment days_in_stock for all records (if you want global update).
        """
        cls.objects.update(days_in_stock=F('days_in_stock') + 1)
