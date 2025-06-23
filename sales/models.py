from django.db import models
from django.db.models import F, Sum
from django.db import transaction
from django.db import OperationalError
from products.models import Product
from customers.models import Customer
from accounts.models import User
from decimal import Decimal
from django.db.models import DecimalField
from django.apps import apps
from products.models import User, ClientSubscription

import time
import logging

logger = logging.getLogger(__name__)




from django.db import models, transaction
from django.db.models import F, Sum, DecimalField
from django.db.utils import OperationalError








from django.conf import settings  # Import settings for AUTH_USER_MODEL




logger = logging.getLogger(__name__)

class Order(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    ]

    PAYMENT_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
        ('transfer', 'Bank Transfer'),
        ('mobile', 'Mobile Payment'),
    ]

    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='orders'
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='orders'
    )

    subscription = models.ForeignKey(
        ClientSubscription,
        on_delete=models.PROTECT,
        related_name='orders',
        null=True, blank=True
    )

    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cash', blank=True)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=8)   # percent
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)   # percent

    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    change_given = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        user_name = self.user.get_full_name() if self.user else "Unknown User"
        return f"Order #{self.id} - {user_name}"

    def calculate_total(self):
        """
        Recompute self.total = (sum of items) - discount + tax, save and return it.
        """
        try:
            with transaction.atomic():
                agg = self.items.aggregate(
                    subtotal=Sum(F('price') * F('quantity'), output_field=DecimalField())
                )
                subtotal = agg['subtotal'] or Decimal('0')
                discount_amount = subtotal * (self.discount / Decimal('100'))
                tax_amount = (subtotal - discount_amount) * (self.tax_rate / Decimal('100'))
                new_total = (subtotal - discount_amount) + tax_amount

                self.total = new_total
                self.save(update_fields=['total'])
                return self.total

        except Exception as e:
            logger.error(f"Failed to calculate total: {e}")
            raise

    def calculate_change(self):
        """
        Compute change_given = max(0, amount_paid - total), save with retries.
        """
        if self.amount_paid <= Decimal('0'):
            return self.change_given

        self.change_given = max(Decimal('0'), self.amount_paid - self.total)
        retries = 3
        delay = 0.1
        for i in range(retries):
            try:
                self.save(update_fields=['change_given'])
                return self.change_given
            except OperationalError as e:
                if 'database is locked' in str(e).lower() and i < retries - 1:
                    time.sleep(delay * (2 ** i))
                    continue
                logger.error(f"Change calculation failed: {e}")
                if i == retries - 1:
                    raise
        return self.change_given

    def update_inventory(self):
        """
        For each OrderItem, decrement product.stock (or set to zero if insufficient),
        with optimistic locking and retries.
        """
        if self.status != 'completed':
            return

        retries = 5
        delay = 0.1
        for i in range(retries):
            try:
                with transaction.atomic():
                    for item in self.items.select_related('product').select_for_update():
                        prod = item.product
                        updated = prod.__class__.objects.filter(
                            id=prod.id,
                            stock__gte=item.quantity
                        ).update(stock=F('stock') - item.quantity)
                        if updated == 0:
                            # Not enough stock, set to zero
                            prod.__class__.objects.filter(id=prod.id).update(stock=0)
                            logger.warning(f"Insufficient stock for {prod.name}; set to 0.")
                return
            except OperationalError as e:
                if 'database is locked' in str(e).lower() and i < retries - 1:
                    time.sleep(delay * (2 ** i))
                    continue
                logger.error(f"Inventory update failed: {e}")
                if i == retries - 1:
                    raise
            except Exception as e:
                logger.error(f"Unexpected error updating inventory: {e}")
                if i == retries - 1:
                    raise

    def generate_receipt(self):
        """
        Returns a plain-text receipt for this order.
        """
        from .models import OrderItem  # avoid circular import
        from django.conf import settings
        symbol = getattr(settings, 'CURRENCY_SYMBOL', '$')
        
         
        items = self.items.select_related('product').all()
        lines = []
        for item in items:
            lines.append(
               f"{item.quantity} × {item.product.name} @ {symbol}{item.price:.2f} = {symbol}{item.total_price:.2f}"
        )

        subtotal = sum(item.total_price for item in items)
        discount_amount = subtotal * (self.discount / Decimal('100'))
        tax_amount = (subtotal - discount_amount) * (self.tax_rate / Decimal('100'))

        header = [
            f"RECEIPT #{self.id}",
            f"Date: {self.created_at.strftime('%Y-%m-%d %H:%M')}",
            f"Customer: {(self.customer.name if self.customer else 'Walk-in')}",
            f"Cashier: {(self.user.get_full_name() if self.user else 'Unknown')}",
            "",
            "ITEMS:"
        ]

        footer = [
            "",
            f"Subtotal: {symbol}{subtotal:.2f}"
            f"Discount ({self.discount}%): -{symbol}{discount_amount:.2f}",
            f"Tax ({self.tax_rate}%): +{symbol}{tax_amount:.2f}",
            "-----------------------",
            f"TOTAL: {symbol}{self.total:.2f}",
            f"Amount Paid: {symbol}{self.amount_paid:.2f}",
            f"Change: {symbol}{self.change_given:.2f}",
            f"Payment Method: {self.get_payment_method_display()}",
            "",
            "Thank you for your purchase!"
        ]

        return "\n".join(header + lines + footer)


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.PROTECT
    )
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # snapshot
    total_price = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        ordering = ['-order__created_at']

    class Meta:
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['product']),
        ]
        # Add unique together constraint to prevent duplicates
        unique_together = ('order', 'product')

    @property
    def total_price(self):
        """Calculate total price for this item"""
        return self.price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.name} (Order #{self.order.id})"
    
