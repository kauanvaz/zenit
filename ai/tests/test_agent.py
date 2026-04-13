import datetime
from unittest.mock import patch, MagicMock
from django.test import TestCase
from decimal import Decimal
from users.models import User
from ai.models import FinancialAnalysis
from ai.agents.financial_analyst import run_analysis
from transactions.models import Transaction
from accounts.models import Account
from categories.models import Category

def make_user(email='user@test.com'):
    return User.objects.create_user(
        email=email,
        password='password123',
        first_name='Test',
        last_name='User'
    )

class AgentIntegrationTests(TestCase):
    """Tests for the AI Agent integration and run_analysis function."""

    def setUp(self):
        self.user = make_user()
        self.period = '2026-04'
        
        # Criar dados reais para os snapshots
        self.account = Account.objects.create(user=self.user, name='Bank', type='checking', initial_balance=0)
        self.cat_inc = Category.objects.create(user=self.user, name='In', type='income')
        self.cat_exp = Category.objects.create(user=self.user, name='Out', type='expense')
        
        Transaction.objects.create(
            user=self.user, account=self.account, category=self.cat_inc,
            amount=Decimal('5000.00'), type='income', date=datetime.date(2026, 4, 1)
        )
        Transaction.objects.create(
            user=self.user, account=self.account, category=self.cat_exp,
            amount=Decimal('2000.00'), type='expense', date=datetime.date(2026, 4, 2)
        )

    @patch('ai.agents.financial_analyst._get_agent_executor')
    def test_run_analysis_success(self, mock_get_executor):
        # Mock do AgentExecutor
        mock_executor = MagicMock()
        mock_executor.invoke.return_value = {
            'output': 'Tudo sob controle! Sua saúde financeira está ótima.'
        }
        mock_get_executor.return_value = mock_executor
        
        # Executar análise (vai usar os dados reais do setUp para os snapshots)
        analysis = run_analysis(self.user.id, self.period)
        
        self.assertEqual(analysis.status, 'completed')
        self.assertEqual(analysis.analysis_text, 'Tudo sob controle! Sua saúde financeira está ótima.')
        self.assertEqual(analysis.total_income, Decimal('5000.00'))
        self.assertEqual(analysis.total_expenses, Decimal('2000.00'))
        self.assertEqual(analysis.net_balance, Decimal('3000.00'))
        self.assertEqual(analysis.user, self.user)
        self.assertEqual(analysis.period, self.period)

    @patch('ai.agents.financial_analyst.AgentExecutor.invoke')
    def test_run_analysis_failure(self, mock_invoke):
        # Simular erro na chamada do agente
        # Nota: Como run_analysis chama _get_agent_executor, 
        # o mock_invoke aqui só funciona se _get_agent_executor retornar um objeto cujo invoke é esse mock.
        # É melhor mockar _get_agent_executor.
        with patch('ai.agents.financial_analyst._get_agent_executor') as mock_get_exec:
            mock_exec = MagicMock()
            mock_exec.invoke.side_effect = Exception('OpenAI API Error')
            mock_get_exec.return_value = mock_exec
            
            analysis = run_analysis(self.user.id, self.period)
            
            self.assertEqual(analysis.status, 'failed')
            self.assertIn('OpenAI API Error', analysis.error_message)

    def test_run_analysis_creates_pending_record_first(self):
        # Testar se ele cria o registro antes de processar
        with patch('ai.agents.financial_analyst._get_agent_executor') as mock_get_exec:
            mock_exec = MagicMock()
            mock_exec.invoke.return_value = {'output': 'ok'}
            mock_get_exec.return_value = mock_exec
            
            run_analysis(self.user.id, self.period)
            
            self.assertTrue(FinancialAnalysis.objects.filter(
                user=self.user, period=self.period
            ).exists())
