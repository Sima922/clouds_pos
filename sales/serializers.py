from rest_framework import serializers
from django.db import transaction
from .models import Order, OrderItem
from products.models import Product
from customers.models import Customer

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    stock = serializers.IntegerField(source='product.stock', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'quantity', 'price', 'stock']
        extra_kwargs = {
            'product': {'required': True},
            'quantity': {'min_value': 1}
        }

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True, required=False)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    
    # Add fields for payment tracking
    amount_paid = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=0)
    change_given = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=0)
    update_inventory = serializers.BooleanField(required=False, default=True, write_only=True)
    
    def validate(self, data):
        items = data.get('items', [])
        product_ids = [item['product'].id for item in items]
        
        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError("Duplicate products in order items")
            
        return data
    
    class Meta:
        model = Order
        fields = [
            'id', 'customer', 'customer_name', 'user', 'total', 
            'status', 'tax_rate', 'discount', 'items', 'created_at',
            'payment_method', 'amount_paid', 'change_given', 'update_inventory'
        ]
        read_only_fields = ['total', 'created_at', 'user', 'change_given']
        extra_kwargs = {
            'customer': {'required': False},
            'payment_method': {'required': False}
        }

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        update_inventory = validated_data.pop('update_inventory', True)
        
        # Extract amount paid for change calculation
        amount_paid = validated_data.get('amount_paid', 0)
        
        order = Order.objects.create(**validated_data)
        
        for item_data in items_data:
            product = item_data['product']
            quantity = item_data['quantity']
            
            if product.stock < quantity:
                raise serializers.ValidationError({
                    'error': f"Insufficient stock for {product.name}. Available: {product.stock}"
                })
            
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=product.price
            )

        # Calculate the total first
        order.calculate_total()
        
        # Calculate change if amount paid is provided
        if amount_paid > 0:
            order.calculate_change()
        
        # Update inventory if requested and order is completed
        if update_inventory and order.status == 'completed':
            order.update_inventory()
            
        return order
    