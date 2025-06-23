from rest_framework import serializers
from .models import SalesReport, InventoryAgingReport
from products.models import Product, Category

class InventoryAgingSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name')
    sku = serializers.CharField(source='product.sku')
    current_stock = serializers.IntegerField(source='product.stock')

    class Meta:
        model = InventoryAgingReport
        fields = [
            'product_name', 
            'sku',
            'date_received',
            'days_in_stock',
            'quantity',
            'current_stock'
        ]

class SalesReportExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesReport
        fields = [
            'report_date',
            'start_date',
            'end_date',
            'total_sales',
            'total_orders',
            'total_items_sold',
            'average_order_value'
        ]

# Keep existing serializers and add export fields
class SalesSummarySerializer(serializers.Serializer):
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    total_sales = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_orders = serializers.IntegerField()
    avg_order_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    top_products = serializers.ListField(child=serializers.DictField())
    sales_by_category = serializers.ListField(child=serializers.DictField())
    export_formats = serializers.ListField(child=serializers.CharField())
    