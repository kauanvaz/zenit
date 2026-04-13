from django import forms
from django.db.models import Q
from .models import Transaction
from accounts.models import Account
from categories.models import Category


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = [
            'account', 'category', 'description',
            'amount', 'type', 'date', 'notes'
        ]
        widgets = {
            'account': forms.Select(attrs={
                'class': 'bg-slate-900 border-none text-slate-100 rounded-lg w-full px-4 py-3 focus:ring-2 focus:ring-emerald-500'
            }),
            'category': forms.Select(attrs={
                'class': 'bg-slate-900 border-none text-slate-100 rounded-lg w-full px-4 py-3 focus:ring-2 focus:ring-emerald-500'
            }),
            'description': forms.TextInput(attrs={
                'class': 'bg-slate-900 border-none text-slate-100 rounded-lg w-full px-4 py-3 focus:ring-2 focus:ring-emerald-500',
                'placeholder': 'Descreva a transação (ex: Almoço)'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'bg-slate-900 border-none text-slate-100 rounded-lg w-full px-4 py-3 focus:ring-2 focus:ring-emerald-500',
                'step': '0.01'
            }),
            'type': forms.Select(attrs={
                'class': 'bg-slate-900 border-none text-slate-100 rounded-lg w-full px-4 py-3 focus:ring-2 focus:ring-emerald-500'
            }),
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'bg-slate-900 border-none text-slate-100 rounded-lg w-full px-4 py-3 focus:ring-2 focus:ring-emerald-500'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'bg-slate-900 border-none text-slate-100 rounded-lg w-full px-4 py-3 focus:ring-2 focus:ring-emerald-500',
                'rows': 3,
                'placeholder': 'Opcional: Detalhes extras sobre esta transação'
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            self.fields['account'].queryset = Account.objects.filter(user=user)
            self.fields['category'].queryset = Category.objects.filter(
                Q(user=user) | Q(user=None)
            )
