from django.contrib import admin

from .models import FinancialAnalysis


@admin.register(FinancialAnalysis)
class FinancialAnalysisAdmin(admin.ModelAdmin):
    list_display = ('user', 'period', 'status', 'total_income', 'total_expenses', 'created_at')
    list_filter = ('status', 'period')
    search_fields = ('user__email', 'period')
    readonly_fields = ('created_at', 'updated_at', 'analysis_text', 'error_message')
    ordering = ('-created_at',)
