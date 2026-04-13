from django import forms
from .models import Account


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['name', 'type', 'initial_balance', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'bg-slate-900 border-none text-slate-100 rounded-lg w-full px-4 py-3 focus:ring-2 focus:ring-emerald-500',
                'placeholder': 'Nome da conta (ex: Nubank)'
            }),
            'type': forms.Select(attrs={
                'class': 'bg-slate-900 border-none text-slate-100 rounded-lg w-full px-4 py-3 focus:ring-2 focus:ring-emerald-500'
            }),
            'initial_balance': forms.NumberInput(attrs={
                'class': 'bg-slate-900 border-none text-slate-100 rounded-lg w-full px-4 py-3 focus:ring-2 focus:ring-emerald-500',
                'step': '0.01'
            }),
            'description': forms.Textarea(attrs={
                'class': 'bg-slate-900 border-none text-slate-100 rounded-lg w-full px-4 py-3 focus:ring-2 focus:ring-emerald-500',
                'rows': 3,
                'placeholder': 'Opcional: Detalhes sobre esta conta'
            }),
        }
