from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from users.models import User


class RegisterForm(UserCreationForm):
    """Registration form for new users using email as the unique identifier."""

    first_name = forms.CharField(
        label='Primeiro nome',
        max_length=150,
        widget=forms.TextInput(attrs={'autocomplete': 'given-name'}),
    )
    last_name = forms.CharField(
        label='Sobrenome',
        max_length=150,
        widget=forms.TextInput(attrs={'autocomplete': 'family-name'}),
    )
    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={'autocomplete': 'email'}),
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password1', 'password2']

    def clean_email(self):
        """Validate that the email address is not already registered."""
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Este e-mail já está cadastrado.')
        return email


class CustomAuthenticationForm(AuthenticationForm):
    """Authentication form that uses email instead of username."""

    username = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={'autocomplete': 'email'}),
    )
