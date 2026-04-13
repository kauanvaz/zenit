import datetime
from decimal import Decimal
from unittest.mock import patch
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from accounts.models import Account
from categories.models import Category
from transactions.models import Transaction
from users.models import User
from ai.models import FinancialAnalysis

def make_user(email='user@test.com'):
    return User.objects.create_user(
        email=email,
        password='password123',
        first_name='Test',
        last_name='User'
    )

class AIViewTests(TestCase):
    """Tests for the AI app views."""

    def setUp(self):
        self.user = make_user()
        self.client = Client()
        self.url = reverse('ai:analyze')

    def _create_transactions_for_current_period(self, quantity=3):
        account = Account.objects.create(
            user=self.user,
            name='Conta teste',
            type='checking',
            initial_balance=Decimal('0'),
        )
        income_cat = Category.objects.create(user=self.user, name='Salário', type='income')
        expense_cat = Category.objects.create(user=self.user, name='Mercado', type='expense')

        for i in range(quantity):
            Transaction.objects.create(
                user=self.user,
                account=account,
                category=income_cat if i % 2 == 0 else expense_cat,
                amount=Decimal('100.00'),
                type='income' if i % 2 == 0 else 'expense',
                date=timezone.now().date(),
                description=f'Transação {i + 1}',
            )

    def test_trigger_analysis_unauthenticated_redirects(self):
        # Deve redirecionar para o login
        response = self.client.post(self.url)
        self.assertRedirects(response, f'/auth/login/?next={self.url}')

    @patch('ai.views.run_analysis')
    def test_trigger_analysis_first_time_success(self, mock_run):
        # Primeira análise do usuário
        self.client.login(username='user@test.com', password='password123')
        self._create_transactions_for_current_period(quantity=3)
        
        # Garantir que o período gerado no teste seja o mesmo da view
        with patch('ai.views.timezone.now') as mock_now:
            mock_now.return_value = datetime.datetime(2026, 4, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
            period = mock_now.return_value.strftime('%Y-%m')
            
            response = self.client.post(self.url)
            
            # Deve redirecionar ao dashboard com mensagem de sucesso
            self.assertRedirects(response, reverse('dashboard'))
            mock_run.assert_called_once_with(user_id=self.user.id, period=period)

    @patch('ai.views.run_analysis')
    def test_trigger_analysis_stale_allowed(self, mock_run):
        # Uma análise antiga (mais de 24h) existe, deve permitir rodar de novo
        self.client.login(username='user@test.com', password='password123')
        self._create_transactions_for_current_period(quantity=3)
        
        analysis = FinancialAnalysis.objects.create(
            user=self.user,
            period=timezone.now().strftime('%Y-%m'),
            status='completed',
            analysis_text='Análise velha'
        )
        # Forçar created_at para 25 horas atrás
        old_time = timezone.now() - datetime.timedelta(hours=25)
        FinancialAnalysis.objects.filter(pk=analysis.pk).update(created_at=old_time)
        
        response = self.client.post(self.url)
        
        self.assertRedirects(response, reverse('dashboard'))
        # mock_run deve ser chamado
        mock_run.assert_called_once()

    @patch('ai.views.run_analysis')
    def test_trigger_analysis_recent_throttled(self, mock_run):
        # Uma análise recente (menos de 24h) existe, deve bloquear
        self.client.login(username='user@test.com', password='password123')
        
        FinancialAnalysis.objects.create(
            user=self.user,
            period=timezone.now().strftime('%Y-%m'),
            status='completed',
            analysis_text='Análise recente'
        )
        
        response = self.client.post(self.url)
        
        # Deve redirecionar com mensagem mas SEM chamar run_analysis
        self.assertRedirects(response, reverse('dashboard'))
        mock_run.assert_not_called()
        
        # Verificar se uma mensagem de erro/info foi disparada (o Django armazena no cookie)
        # Como o Client não carrega as mensagens diretamente no response.content, 
        # verificamos se run_analysis não foi chamado, que é a prova real.

    @patch('ai.views.run_analysis')
    def test_trigger_analysis_wrong_period_allowed(self, mock_run):
        # Uma análise recente para OUTRO período (ex: mês passado) não deve bloquear o mês atual
        self.client.login(username='user@test.com', password='password123')
        self._create_transactions_for_current_period(quantity=3)
        
        last_month = (timezone.now().replace(day=1) - datetime.timedelta(days=1)).strftime('%Y-%m')
        FinancialAnalysis.objects.create(
            user=self.user,
            period=last_month,
            status='completed'
        )
        
        response = self.client.post(self.url)
        
        self.assertRedirects(response, reverse('dashboard'))
        # Deve chamar run_analysis para o período atual
        mock_run.assert_called_once()

    @patch('ai.views.run_analysis')
    def test_trigger_analysis_shows_generated_text_on_dashboard(self, mock_run):
        # Ao gerar análise, o usuário deve visualizá-la após o redirect.
        self.client.login(username='user@test.com', password='password123')

        analysis = FinancialAnalysis.objects.create(
            user=self.user,
            period=timezone.now().strftime('%Y-%m'),
            status=FinancialAnalysis.Status.COMPLETED,
            analysis_text='Relatório IA de teste',
        )
        mock_run.return_value = analysis

        response = self.client.post(self.url, follow=True)

        self.assertRedirects(response, reverse('dashboard'))
        self.assertContains(response, 'Relatório IA de teste')

    @patch('ai.views.run_analysis')
    def test_trigger_analysis_requires_minimum_three_transactions(self, mock_run):
        # Deve bloquear geração quando houver menos de 3 transações no período.
        self.client.login(username='user@test.com', password='password123')

        account = Account.objects.create(
            user=self.user,
            name='Conta principal',
            type='checking',
            initial_balance=Decimal('0'),
        )
        income_cat = Category.objects.create(user=self.user, name='Salário', type='income')
        expense_cat = Category.objects.create(user=self.user, name='Mercado', type='expense')

        Transaction.objects.create(
            user=self.user,
            account=account,
            category=income_cat,
            amount=Decimal('1000.00'),
            type='income',
            date=timezone.now().date(),
        )
        Transaction.objects.create(
            user=self.user,
            account=account,
            category=expense_cat,
            amount=Decimal('120.00'),
            type='expense',
            date=timezone.now().date(),
        )

        response = self.client.post(self.url, follow=True)

        self.assertRedirects(response, reverse('dashboard'))
        self.assertContains(response, 'pelo menos 3 transações')
        mock_run.assert_not_called()
