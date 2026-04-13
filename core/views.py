"""
Core views for the Zenit project.

Contains the public home view and the main dashboard view with KPIs
and recent transactions for the authenticated user.
"""
from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.utils import timezone
from django.views.generic import TemplateView

class HomeView(TemplateView):
    """Public home page.

    Redirects authenticated users to the dashboard.
    """

    template_name = 'home.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            from django.shortcuts import redirect
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)


class DashboardView(LoginRequiredMixin, TemplateView):
    """Main dashboard view with KPIs and recent transactions. Protected route"""

    template_name = 'dashboard/index.html'

    def get_context_data(self, **kwargs):
        from accounts.models import Account
        from ai.models import FinancialAnalysis
        from transactions.models import Transaction

        context = super().get_context_data(**kwargs)
        user = self.request.user
        now = timezone.now()
        current_period = now.strftime('%Y-%m')

        # Total balance - Account.current_balance is a Python property,
        # so aggregation must be done in Python, not at the DB level
        user_accounts = Account.objects.filter(user=user)
        total_balance = sum(
            (account.current_balance for account in user_accounts),
            Decimal('0'),
        )

        # Monthly income and expenses - amount is a real DB field, so we
        # can use aggregate(Sum) for efficiency
        monthly_qs = Transaction.objects.filter(
            user=user,
            date__year=now.year,
            date__month=now.month,
        )

        monthly_income_result = monthly_qs.filter(type='income').aggregate(
            total=Sum('amount')
        )
        monthly_income = monthly_income_result['total'] or Decimal('0')

        monthly_expenses_result = monthly_qs.filter(type='expense').aggregate(
            total=Sum('amount')
        )
        monthly_expenses = monthly_expenses_result['total'] or Decimal('0')

        # Five most recent transactions for this user
        recent_transactions = Transaction.objects.filter(user=user).order_by(
            '-date', '-created_at'
        )[:5]

        latest_analysis = FinancialAnalysis.objects.filter(
            user=user,
            period=current_period,
            status=FinancialAnalysis.Status.COMPLETED,
        ).first()

        # Is the analysis older than 24 hours?
        stale_cutoff = now - timezone.timedelta(hours=24)
        is_analysis_stale = bool(
            latest_analysis and latest_analysis.created_at < stale_cutoff
        )

        context['total_balance'] = total_balance
        context['monthly_income'] = monthly_income
        context['monthly_expenses'] = monthly_expenses
        context['recent_transactions'] = recent_transactions
        context['current_period'] = current_period
        context['latest_analysis'] = latest_analysis
        context['is_analysis_stale'] = is_analysis_stale
        return context
