from django.contrib import admin
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'description',
        'user',
        'account',
        'category',
        'amount',
        'type',
        'date',
        'created_at'
    )
    list_filter = ('type', 'date', 'account', 'category', 'user')
    search_fields = ('description', 'notes')
    ordering = ('-date', '-created_at')
