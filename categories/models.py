from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    class CategoryType(models.TextChoices):
        INCOME = 'income', _('Receita')
        EXPENSE = 'expense', _('Despesa')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='categories',
        null=True,
        blank=True,
        help_text=_('Null for global categories.')
    )
    name = models.CharField(max_length=100)
    type = models.CharField(
        max_length=10,
        choices=CategoryType.choices,
        default=CategoryType.EXPENSE
    )
    color = models.CharField(
        max_length=7,
        default='#334155',
        help_text=_('Hex color (e.g., #000000).')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Categoria')
        verbose_name_plural = _('Categorias')
        ordering = ['name']
        indexes = [
            models.Index(fields=['user', 'type']),
        ]

    def __str__(self):
        return f'{self.name} ({self.get_type_display()})'
