from django.core.management.base import BaseCommand
from django.urls import reverse, NoReverseMatch
from django.test import Client
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Test URL resolution for sales app'

    def handle(self, *args, **options):
        self.stdout.write('Testing URL resolution...\n')
        
        # Test URL patterns
        test_urls = [
            '/api/orders/',
            '/pos/api/orders/',
            '/api/orders/1/receipt/',
            '/pos/api/orders/1/receipt/',
        ]
        
        client = Client()
        
        for url in test_urls:
            try:
                response = client.get(url)
                self.stdout.write(f'{url}: Status {response.status_code}')
            except Exception as e:
                self.stdout.write(f'{url}: Error - {e}')
        
        # Test reverse URL resolution
        try:
            url = reverse('sales:order-receipt', kwargs={'order_id': 1})
            self.stdout.write(f'Reverse URL for order-receipt: {url}')
        except NoReverseMatch as e:
            self.stdout.write(f'Reverse URL failed: {e}')
        
        self.stdout.write('\nURL testing complete!')