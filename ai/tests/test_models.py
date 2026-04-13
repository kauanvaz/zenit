from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from users.models import User
from ai.models import FinancialAnalysis

def make_user(email='user@test.com', password='pass123word!'):
    return User.objects.create_user(
        email=email,
        password=password,
        first_name='Test',
        last_name='User',
    )

class FinancialAnalysisModelTests(TestCase):
    """Tests for the FinancialAnalysis model."""

    def setUp(self):
        self.user = make_user()
        self.other_user = make_user(email='other@test.com')

    def test_analysis_creation(self):
        analysis = FinancialAnalysis.objects.create(
            user=self.user,
            period='2026-04',
            status='completed',
            analysis_text='Test analysis',
            total_income=Decimal('1000.00'),
            total_expenses=Decimal('500.00'),
            net_balance=Decimal('500.00'),
        )
        self.assertEqual(analysis.user, self.user)
        self.assertEqual(analysis.period, '2026-04')
        self.assertEqual(analysis.status, 'completed')
        self.assertIsNotNone(analysis.created_at)
        self.assertIsNotNone(analysis.updated_at)

    def test_str_representation(self):
        analysis = FinancialAnalysis.objects.create(
            user=self.user,
            period='2026-04',
            status='pending',
        )
        expected_str = f'Análise de {self.user.email} - 2026-04 (pending)'
        self.assertEqual(str(analysis), expected_str)

    def test_ordering_by_created_at_desc(self):
        # Criação de duas análises em tempos diferentes
        a1 = FinancialAnalysis.objects.create(user=self.user, period='2026-03', status='completed')
        a2 = FinancialAnalysis.objects.create(user=self.user, period='2026-04', status='completed')
        
        latest = FinancialAnalysis.objects.filter(user=self.user).first()
        # Devido ao ordering por -created_at, a segunda criada deve ser a primeira retornada
        self.assertEqual(latest, a2)

    def test_user_isolation(self):
        FinancialAnalysis.objects.create(user=self.user, period='2026-04', status='completed')
        FinancialAnalysis.objects.create(user=self.other_user, period='2026-04', status='completed')
        
        self.assertEqual(FinancialAnalysis.objects.filter(user=self.user).count(), 1)
        self.assertEqual(FinancialAnalysis.objects.filter(user=self.other_user).count(), 1)
