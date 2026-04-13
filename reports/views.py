"""
Reports views for Zenit.

Provides aggregated transaction data for charts:
- Monthly income vs expense for the last 12 months (bar chart)
- Expense totals grouped by category for the current year (pie chart)
"""
import json
from datetime import date

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.views.generic import TemplateView

from transactions.models import Transaction

MONTH_LABELS_PT = [
    'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
    'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez',
]


def _last_12_months(reference: date) -> list[tuple[int, int]]:
    """Return a list of (year, month) tuples for the last 12 months.

    The list starts 11 months before `reference` and ends on `reference`'s
    month (inclusive), preserving chronological order.
    """
    months = []
    year = reference.year
    month = reference.month
    for _ in range(12):
        months.append((year, month))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return list(reversed(months))


class ReportsView(LoginRequiredMixin, TemplateView):
    """Render the reports page with chart data passed as JSON context."""

    template_name = 'reports/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = date.today()

        # Monthly income / expense - last 12 months
        month_periods = _last_12_months(today)

        monthly_labels = []
        monthly_income = []
        monthly_expenses = []

        for year, month in month_periods:
            label = f'{MONTH_LABELS_PT[month - 1]} {year}'
            monthly_labels.append(label)

            income_total = (
                Transaction.objects
                .filter(user=user, date__year=year, date__month=month, type='income')
                .aggregate(total=Sum('amount'))['total']
            )
            monthly_income.append(float(income_total or 0))

            expense_total = (
                Transaction.objects
                .filter(user=user, date__year=year, date__month=month, type='expense')
                .aggregate(total=Sum('amount'))['total']
            )
            monthly_expenses.append(float(expense_total or 0))

        # Category expenses - current year
        category_qs = (
            Transaction.objects
            .filter(user=user, type='expense', date__year=today.year)
            .exclude(category__isnull=True)
            .values('category__name', 'category__color')
            .annotate(total=Sum('amount'))
            .order_by('-total')
        )

        category_labels = [row['category__name'] for row in category_qs]
        category_data = [float(row['total']) for row in category_qs]
        category_colors = [row['category__color'] for row in category_qs]

        context.update({
            'monthly_labels': json.dumps(monthly_labels),
            'monthly_income': json.dumps(monthly_income),
            'monthly_expenses': json.dumps(monthly_expenses),
            'category_labels': json.dumps(category_labels),
            'category_data': json.dumps(category_data),
            'category_colors': json.dumps(category_colors),
        })
        return context
