import datetime
from decimal import Decimal
from unittest.mock import patch
from django.test import TestCase
from users.models import User
from accounts.models import Account
from categories.models import Category
from transactions.models import Transaction
from ai.agents.tools import build_tools

def make_user(email='user@test.com'):
    return User.objects.create_user(
        email=email,
        password='password123',
        first_name='Test',
        last_name='User'
    )

class AgentToolsTests(TestCase):
    """Tests for the AI agent tools by executing them from build_tools."""

    def setUp(self):
        self.user = make_user()
        self.other_user = make_user(email='other@test.com')
        
        # Obter as tools vinculadas ao usuário de teste
        tools_list = build_tools(self.user.id)
        self.tools = {tool.name: tool for tool in tools_list}
        
        # Criar conta, categoria e transação para o usuário de teste
        self.account = Account.objects.create(
            user=self.user,
            name='Test Account',
            type='checking',
            initial_balance=Decimal('100.00')
        )
        self.category_income = Category.objects.create(
            user=self.user,
            name='Salary',
            type='income'
        )
        self.category_expense = Category.objects.create(
            user=self.user,
            name='Food',
            type='expense'
        )
        
        # Transação de Receita em 2026-04
        Transaction.objects.create(
            user=self.user,
            account=self.account,
            category=self.category_income,
            description='Salary payout',
            amount=Decimal('5000.00'),
            type='income',
            date=datetime.date(2026, 4, 1)
        )
        
        # Transação de Despesa em 2026-04
        Transaction.objects.create(
            user=self.user,
            account=self.account,
            category=self.category_expense,
            description='Dinner',
            amount=Decimal('150.00'),
            type='expense',
            date=datetime.date(2026, 4, 2)
        )
        
        # Transação para outro usuário
        other_account = Account.objects.create(user=self.other_user, name='Other', type='checking', initial_balance=Decimal('0'))
        Transaction.objects.create(
            user=self.other_user,
            account=other_account,
            category=Category.objects.create(user=self.other_user, name='Other', type='expense'),
            amount=Decimal('100.00'),
            type='expense',
            date=datetime.date(2026, 4, 1)
        )

    def test_get_transactions_summary_isolation(self):
        # A tool deve filtrar apenas as transações do usuário passado via closure
        tool = self.tools['get_transactions_summary']
        summary = tool.invoke({'period': '2026-04'})
        
        self.assertEqual(summary['total_income'], 5000.0)
        self.assertEqual(summary['total_expenses'], 150.0)
        self.assertEqual(summary['net_balance'], 4850.0)
        self.assertEqual(summary['transaction_count'], 2)

    def test_get_accounts_summary(self):
        tool = self.tools['get_accounts_summary']
        summary = tool.invoke({})
        
        # Deve ter a conta que criamos
        self.assertEqual(len(summary), 1)
        self.assertEqual(summary[0]['name'], 'Test Account')
        # Saldo: initial(100) + income(5000) - expense(150) = 4950
        self.assertEqual(summary[0]['current_balance'], 4950.0)

    def test_get_top_expenses(self):
        tool = self.tools['get_top_expenses']
        
        # Criar mais uma despesa na categoria 'Food' e uma em 'Rent'
        rent_cat = Category.objects.create(user=self.user, name='Rent', type='expense')
        Transaction.objects.create(
            user=self.user, account=self.account, category=self.category_expense,
            amount=Decimal('50.00'), type='expense', date=datetime.date(2026, 4, 5)
        )
        Transaction.objects.create(
            user=self.user, account=self.account, category=rent_cat,
            amount=Decimal('1000.00'), type='expense', date=datetime.date(2026, 4, 5)
        )
        
        top = tool.invoke({'period': '2026-04', 'limit': 2})
        # Rent deve ser a primeira (1000), Food a segunda (150 + 50 = 200)
        self.assertEqual(len(top), 2)
        self.assertEqual(top[0]['category_name'], 'Rent')
        self.assertEqual(top[0]['total_spent'], 1000.0)
        self.assertEqual(top[1]['category_name'], 'Food')
        self.assertEqual(top[1]['total_spent'], 200.0)

    def test_get_monthly_trend(self):
        tool = self.tools['get_monthly_trend']
        
        # Criar transação em março (considerando que hoje é abril/2026 nos testes)
        # O tool calcula meses baseado no 'date.today()'
        with patch('ai.agents.tools.date') as mock_date:
            mock_date.today.return_value = datetime.date(2026, 4, 15)
            # Re-mockar transactions se necessário, mas as ferramentas usam ORM direto
            Transaction.objects.create(
                user=self.user, account=self.account, category=self.category_expense,
                amount=Decimal('100.00'), type='expense', date=datetime.date(2026, 3, 15)
            )
            
            trend = tool.invoke({'months': 2})
            self.assertEqual(len(trend), 2)
            periods = [t['period'] for t in trend]
            self.assertIn('2026-04', periods)
            self.assertIn('2026-03', periods)
