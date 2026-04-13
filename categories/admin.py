from django.contrib import admin
from .models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'type', 'color', 'created_at')
    list_filter = ('user', 'type', 'created_at')
    search_fields = ('name',)
    ordering = ('name',)
