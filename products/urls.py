from django.urls import path
from .views import (
    ProductListView,
    ProductCreateView,
    ProductUpdateView,
    ProductDeleteView
)

urlpatterns = [
    path('', ProductListView.as_view(), name='product-list'),
    path('create/', ProductCreateView.as_view(), name='product-create'),
    path('update/<int:pk>/', ProductUpdateView.as_view(), name='product-update'),
    path('delete/<int:pk>/', ProductDeleteView.as_view(), name='product-delete'),
]