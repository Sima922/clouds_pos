from django.db import models
from accounts.models import User, ClientSubscription

class Customer(models.Model):
    subscription = models.ForeignKey(ClientSubscription, on_delete=models.CASCADE, related_name='customers', null=True, blank=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name