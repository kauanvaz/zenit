from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.utils import timezone
from django.views import View

from .agents import run_analysis
from .models import FinancialAnalysis

MIN_TRANSACTIONS_FOR_ANALYSIS = 3


class TriggerAnalysisView(LoginRequiredMixin, View):
    """
    Dispara a análise financeira para o usuário autenticado.

    - Aceita apenas POST.
    - Verifica se já existe análise recente (< 24h) para evitar chamadas
      desnecessárias à API OpenAI.
    - Exige no mínimo 3 transações no período solicitado antes de gerar
      uma nova análise.
    - Redireciona ao dashboard após execução.
    """

    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        now = timezone.now()
        period = request.POST.get('period') or now.strftime('%Y-%m')

        # Reutiliza análise recente se existir
        cutoff = now - timezone.timedelta(hours=24)
        recent = FinancialAnalysis.objects.filter(
            user=request.user,
            period=period,
            status=FinancialAnalysis.Status.COMPLETED,
            created_at__gte=cutoff,
        ).first()

        if recent:
            messages.info(request, 'Você já possui uma análise recente para este período.')
            return redirect('dashboard')

        try:
            year, month = int(period[:4]), int(period[5:7])
        except (ValueError, IndexError):
            messages.error(request, 'Período inválido. Use o formato YYYY-MM.')
            return redirect('dashboard')

        from transactions.models import Transaction

        period_transactions_count = Transaction.objects.filter(
            user=request.user,
            date__year=year,
            date__month=month,
        ).count()

        if period_transactions_count < MIN_TRANSACTIONS_FOR_ANALYSIS:
            messages.warning(
                request,
                'Adicione pelo menos 3 transações neste período para gerar a análise.'
            )
            return redirect('dashboard')

        analysis = run_analysis(user_id=request.user.id, period=period)

        if analysis.status == FinancialAnalysis.Status.COMPLETED:
            messages.success(request, 'Análise financeira gerada com sucesso!')
        else:
            messages.error(request, 'Não foi possível gerar a análise. Tente novamente mais tarde.')

        return redirect('dashboard')
