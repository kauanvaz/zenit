from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class CustomUserManager(BaseUserManager):
    """Manager for the custom User model using email as the unique identifier."""

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user with the given email and password."""
        if not email:
            raise ValueError('The email field is required.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model using email as the login identifier instead of username."""

    email = models.EmailField(unique=True, verbose_name='e-mail')
    first_name = models.CharField(max_length=150, verbose_name='primeiro nome')
    last_name = models.CharField(max_length=150, verbose_name='sobrenome')
    is_active = models.BooleanField(default=True, verbose_name='ativo')
    is_staff = models.BooleanField(default=False, verbose_name='equipe')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='atualizado em')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()

    class Meta:
        ordering = ('email',)
        verbose_name = 'usuário'
        verbose_name_plural = 'usuários'

    def __str__(self):
        return self.email

    def get_full_name(self):
        """Return the first and last name separated by a space."""
        return f'{self.first_name} {self.last_name}'.strip()

    def get_short_name(self):
        """Return the first name."""
        return self.first_name
