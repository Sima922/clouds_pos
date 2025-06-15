from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.validators import MinLengthValidator
from .models import User, ClientSubscription

class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name  = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    email      = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    phone      = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        validators=[MinLengthValidator(10)]
    )
    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = User
        fields = ('email','first_name','last_name','phone','role')

    def __init__(self, *args, **kwargs):
        # Expect `creator` kwarg when owner is registering a user
        self.creator = kwargs.pop('creator', None)
        super().__init__(*args, **kwargs)
        for fld in ('password1', 'password2'):
            self.fields[fld].widget.attrs.update({'class': 'form-control'})

    def clean(self):
        data = super().clean()
        # enforce user limit if an owner is creating
        if self.creator and self.creator.role == 'owner':
            sub = self.creator.subscription
            existing = sub.members.exclude(pk=sub.owner_id).count()
            if existing >= sub.user_limit:
                raise forms.ValidationError(
                    f"User limit ({sub.user_limit}) reached for your plan."
                )
        return data

    def save(self, commit=True):
        user = super().save(commit=False)
        # assign new user's subscription to the creator's
        if self.creator and self.creator.subscription:
            user.subscription = self.creator.subscription
        if commit:
            user.save()
        return user
