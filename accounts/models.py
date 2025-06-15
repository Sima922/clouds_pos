from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.validators import MinLengthValidator
from django.utils import timezone
from datetime import timedelta

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class ClientSubscription(models.Model):
    BUSINESS_TIERS = (
        ('basic', 'Basic (1 Register)'),
        ('premium', 'Premium (3 Registers)'),
        ('enterprise', 'Enterprise (Unlimited)'),
    )
    owner = models.OneToOneField(
        'User',
        on_delete=models.CASCADE,
        related_name='owned_subscription',
        limit_choices_to={'role': 'owner'},
        null=True,
        blank=True
    )
    business_name = models.CharField(max_length=255, blank=True)
    tier = models.CharField(max_length=20, choices=BUSINESS_TIERS, default='basic')
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # Remove invalid default; allow null/blank, set in save()
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        # Safe: if business_name provided, use it
        if self.business_name:
            return self.business_name
        # Else if owner exists, use owner's email
        if self.owner:
            return f"{self.owner.email}'s Business"
        # Fallback when neither set
        return "New Subscription"

    def save(self, *args, **kwargs):
        # If business_name blank but owner set, populate default
        if not self.business_name and self.owner:
            self.business_name = f"{self.owner.email}'s Business"
        # If expires_at not set or in past, set default 1 year ahead
        if not self.expires_at or self.expires_at < timezone.now():
            self.expires_at = timezone.now() + timedelta(days=365)
        super().save(*args, **kwargs)

    @property
    def user_limit(self):
        return {'basic': 1, 'premium': 3, 'enterprise': 9999}[self.tier]


class User(AbstractUser):
    ROLE_CHOICES = (
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('cashier', 'Cashier'),
    )
    username = None
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    phone = models.CharField(max_length=20, validators=[MinLengthValidator(10)], default='')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    subscription = models.ForeignKey(
        ClientSubscription,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='members'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone', 'role']

    objects = UserManager()

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"

    def has_perm(self, perm, obj=None):
        if self.is_superuser:
            return True
        return super().has_perm(perm, obj)
