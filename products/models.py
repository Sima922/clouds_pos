from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from accounts.models import User
from accounts.models import User, ClientSubscription

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, 
                               null=True, blank=True, related_name='children')
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return self.name

class Product(models.Model):
    subscription = models.ForeignKey(ClientSubscription, on_delete=models.CASCADE, related_name='products', null=True, blank=True)
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=50, unique=True, default='TEMP-SKU')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products', default=1)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))], default=0)
    stock = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    reorder_level = models.IntegerField(default=5, validators=[MinValueValidator(0)])
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['price']),
        ]

    def __str__(self):
        return f"{self.name} (SKU: {self.sku})"

    @property
    def needs_restock(self):
        return self.stock <= self.reorder_level

class RestockHistory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='restocks')
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    restocked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    restocked_at = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True)

    class Meta:
        ordering = ['-restocked_at']
