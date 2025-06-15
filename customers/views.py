from rest_framework import generics, permissions
from .models import Customer
from .serializers import CustomerSerializer
from rest_framework import generics, permissions
from .models import Customer
from .serializers import CustomerSerializer

class CustomerListCreate(generics.ListCreateAPIView):
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Customer.objects.filter(subscription=self.request.user.subscription)
        return qs

    def perform_create(self, serializer):
        serializer.save(subscription=self.request.user.subscription)

class CustomerDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Customer.objects.filter(subscription=self.request.user.subscription)


class CustomerDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated]