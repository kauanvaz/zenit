from django import forms
from .models import Category


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'type', 'color']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'bg-slate-900 border-none text-slate-100 rounded-lg w-full px-4 py-3 focus:ring-2 focus:ring-emerald-500',
                'placeholder': 'Nome da categoria (ex: Supermercado)'
            }),
            'type': forms.Select(attrs={
                'class': 'bg-slate-900 border-none text-slate-100 rounded-lg w-full px-4 py-3 focus:ring-2 focus:ring-emerald-500'
            }),
            'color': forms.TextInput(attrs={
                'type': 'color',
                'class': 'bg-slate-900 border-none h-12 w-full rounded-lg cursor-pointer focus:ring-2 focus:ring-emerald-500',
            }),
        }
