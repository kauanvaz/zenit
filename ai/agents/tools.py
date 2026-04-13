from datetime import date
from decimal import Decimal

from django.db.models import Sum
from langchain_core.tools import tool


def build_tools(user_id: int) -> list:
    """
    Retorna a lista de tools com user_id vinculado via closure.
    Deve ser chamado uma vez por execução de agente, passando o ID do
    usuário autenticado. Isso garante que o LLM nunca consiga acessar
    dados de outro usuário, mesmo que tente passar um user_id diferente.
    """

    @tool
    def get_transactions_summary(period: str) -> dict:
        """
        Retorna o resumo financeiro do usuário para o período informado.

        Args:
            period: Período no formato 'YYYY-MM' (exemplo: '2026-04').

        Returns:
            Dicionário com total_income, total_expenses, net_balance e
            transaction_count referentes ao período.
        """
        from transactions.models import Transaction

        try:
            year, month = int(period[:4]), int(period[5:7])
        except (ValueError, IndexError):
            return {'error': f'Formato de período inválido: {period}. Use YYYY-MM.'}

        qs = Transaction.objects.filter(
            user_id=user_id,
            date__year=year,
            date__month=month,
        )

        income = qs.filter(type='income').aggregate(total=Sum('amount'))['total'] or Decimal('0')
        expenses = qs.filter(type='expense').aggregate(total=Sum('amount'))['total'] or Decimal('0')

        return {
            'period': period,
            'total_income': float(income),
            'total_expenses': float(expenses),
            'net_balance': float(income - expenses),
            'transaction_count': qs.count(),
        }

    @tool
    def get_accounts_summary() -> list:
        """
        Retorna a lista de contas bancárias do usuário com o saldo atual de cada uma.

        Returns:
            Lista de dicionários com name, type e current_balance de cada conta.
        """
        from accounts.models import Account

        accounts = Account.objects.filter(user_id=user_id)
        return [
            {
                'name': acc.name,
                'type': acc.get_type_display(),
                'current_balance': float(acc.current_balance),
            }
            for acc in accounts
        ]

    @tool
    def get_top_expenses(period: str, limit: int = 5) -> list:
        """
        Retorna as categorias com maior volume de despesas no período.

        Args:
            period: Período no formato 'YYYY-MM'.
            limit: Quantidade de categorias a retornar (padrão: 5).

        Returns:
            Lista de dicionários com category_name e total_spent, ordenada do
            maior para o menor gasto.
        """
        from transactions.models import Transaction

        try:
            year, month = int(period[:4]), int(period[5:7])
        except (ValueError, IndexError):
            return [{'error': f'Formato inválido: {period}'}]

        results = (
            Transaction.objects.filter(
                user_id=user_id,
                type='expense',
                date__year=year,
                date__month=month,
            )
            .values('category__name')
            .annotate(total_spent=Sum('amount'))
            .order_by('-total_spent')[:limit]
        )

        return [
            {
                'category_name': r['category__name'] or 'Sem categoria',
                'total_spent': float(r['total_spent']),
            }
            for r in results
        ]

    @tool
    def get_monthly_trend(months: int = 3) -> list:
        """
        Retorna o histórico financeiro dos últimos N meses completos.

        Args:
            months: Número de meses a retornar (padrão: 3, máximo: 12).

        Returns:
            Lista de dicionários com period, total_income e total_expenses de
            cada mês, ordenada do mais antigo para o mais recente.
        """
        from transactions.models import Transaction

        months = min(int(months), 12)
        today = date.today()
        trend = []

        for i in range(months - 1, -1, -1):
            # Calcula o mês relativo (meses atrás)
            month_offset = today.month - 1 - i
            year = today.year + month_offset // 12
            month = month_offset % 12 + 1

            period = f'{year:04d}-{month:02d}'
            qs = Transaction.objects.filter(
                user_id=user_id,
                date__year=year,
                date__month=month,
            )
            income = qs.filter(type='income').aggregate(total=Sum('amount'))['total'] or Decimal('0')
            expenses = qs.filter(type='expense').aggregate(total=Sum('amount'))['total'] or Decimal('0')

            trend.append({
                'period': period,
                'total_income': float(income),
                'total_expenses': float(expenses),
            })

        return trend

    return [
        get_transactions_summary,
        get_accounts_summary,
        get_top_expenses,
        get_monthly_trend,
    ]
