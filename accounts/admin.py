from django.contrib import admin
from .models import Account


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'type', 'initial_balance', 'current_balance', 'created_at')
    list_filter = ('type', 'user')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
