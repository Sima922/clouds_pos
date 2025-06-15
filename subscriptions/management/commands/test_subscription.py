from django.core.management.base import BaseCommand
from accounts.models import User, ClientSubscription
from django.utils import timezone

class Command(BaseCommand):
    help = 'Creates test subscription for admin user'
    
    def handle(self, *args, **options):
        admin = User.objects.filter(is_superuser=True).first()
        if not admin:
            self.stdout.write(self.style.ERROR('No admin user found'))
            return
            
        ClientSubscription.objects.update_or_create(
            user=admin,
            defaults={
                'tier': 'enterprise',
                'active': True,
                'expires_at': timezone.now() + timezone.timedelta(days=365)
            }
        )
        self.stdout.write(self.style.SUCCESS(f'Created subscription for {admin.email}'))