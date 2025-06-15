from django.contrib import admin
from .models import SalesReport

@admin.register(SalesReport)
class SalesReportAdmin(admin.ModelAdmin):
    list_display = ('report_date', 'start_date', 'end_date', 'total_sales', 'total_orders')
    list_filter = ('report_date',)
    search_fields = ('report_date',)
    readonly_fields = ('created_at',)