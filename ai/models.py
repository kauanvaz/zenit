from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class FinancialAnalysis(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pendente')
        PROCESSING = 'processing', _('Processando')
        COMPLETED = 'completed', _('Concluída')
        FAILED = 'failed', _('Falhou')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='financial_analyses',
    )
    period = models.CharField(
        max_length=7,
        help_text=_('Período no formato YYYY-MM (ex: 2025-04)'),
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    analysis_text = models.TextField(blank=True, default='')
    total_income = models.DecimalField(
        max_digits=19, decimal_places=2, null=True, blank=True
    )
    total_expenses = models.DecimalField(
        max_digits=19, decimal_places=2, null=True, blank=True
    )
    net_balance = models.DecimalField(
        max_digits=19, decimal_places=2, null=True, blank=True
    )
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Análise Financeira')
        verbose_name_plural = _('Análises Financeiras')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'period']),
        ]

    def __str__(self):
        return f'Análise de {self.user} - {self.period} ({self.status})'
