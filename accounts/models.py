from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Account(models.Model):
    class AccountType(models.TextChoices):
        CHECKING = 'checking', _('Corrente')
        SAVINGS = 'savings', _('Poupança')
        WALLET = 'wallet', _('Carteira')
        INVESTMENT = 'investment', _('Investimento')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='accounts'
    )
    name = models.CharField(max_length=100)
    type = models.CharField(
        max_length=20,
        choices=AccountType.choices,
        default=AccountType.CHECKING
    )
    initial_balance = models.DecimalField(
        max_digits=19,
        decimal_places=2,
        default=0.00
    )
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Conta')
        verbose_name_plural = _('Contas')
        ordering = ['name']
        indexes = [
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f'{self.name} ({self.get_type_display()})'

    @property
    def current_balance(self):
        '''
        Calcula o saldo atual dinamicamente:
        Saldo inicial + Soma de Receitas - Soma de Despesas
        '''
        try:
            # Importação local para evitar importação circular
            from transactions.models import Transaction
            income = self.transactions.filter(type='income').aggregate(
                models.Sum('amount')
            )['amount__sum'] or 0
            expense = self.transactions.filter(type='expense').aggregate(
                models.Sum('amount')
            )['amount__sum'] or 0
            return self.initial_balance + income - expense
        except (ImportError, AttributeError, models.ObjectDoesNotExist):
            return self.initial_balance
