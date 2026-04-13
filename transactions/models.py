from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        INCOME = 'income', _('Receita')
        EXPENSE = 'expense', _('Despesa')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    account = models.ForeignKey(
        'accounts.Account',
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    category = models.ForeignKey(
        'categories.Category',
        on_delete=models.SET_NULL,
        related_name='transactions',
        null=True,
        blank=True
    )
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=19, decimal_places=2)
    type = models.CharField(
        max_length=10,
        choices=TransactionType.choices
    )
    date = models.DateField()
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Transação')
        verbose_name_plural = _('Transações')
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['date']),
            models.Index(fields=['account']),
        ]

    def __str__(self):
        return f'{self.description} ({self.amount})'
