from decimal import Decimal

from django.test import Client, TestCase
from django.urls import reverse

from accounts.forms import AccountForm
from accounts.models import Account
from users.models import User


def make_user(email='user@test.com', password='pass123word!'):
    return User.objects.create_user(
        email=email,
        password=password,
        first_name='Test',
        last_name='User',
    )


def make_account(user, name='Nubank', account_type='checking', initial_balance='100.00'):
    return Account.objects.create(
        user=user,
        name=name,
        type=account_type,
        initial_balance=Decimal(initial_balance),
    )


class AccountModelTests(TestCase):
    """Tests for the Account model."""

    def setUp(self):
        self.user = make_user()

    def test_account_creation(self):
        account = make_account(self.user)
        self.assertEqual(account.name, 'Nubank')
        self.assertEqual(account.type, 'checking')
        self.assertEqual(account.initial_balance, Decimal('100.00'))
        self.assertEqual(account.user, self.user)

    def test_str_representation(self):
        account = make_account(self.user, name='Poupança')
        self.assertIn('Poupança', str(account))

    def test_current_balance_no_transactions(self):
        account = make_account(self.user, initial_balance='500.00')
        self.assertEqual(account.current_balance, Decimal('500.00'))

    def test_current_balance_with_income(self):
        from categories.models import Category
        from transactions.models import Transaction
        import datetime

        account = make_account(self.user, initial_balance='100.00')
        category = Category.objects.create(name='Salary', type='income', user=self.user)
        Transaction.objects.create(
            user=self.user,
            account=account,
            category=category,
            description='Salary',
            amount=Decimal('500.00'),
            type='income',
            date=datetime.date.today(),
        )
        self.assertEqual(account.current_balance, Decimal('600.00'))

    def test_current_balance_with_expense(self):
        from categories.models import Category
        from transactions.models import Transaction
        import datetime

        account = make_account(self.user, initial_balance='1000.00')
        category = Category.objects.create(name='Food', type='expense', user=self.user)
        Transaction.objects.create(
            user=self.user,
            account=account,
            category=category,
            description='Lunch',
            amount=Decimal('50.00'),
            type='expense',
            date=datetime.date.today(),
        )
        self.assertEqual(account.current_balance, Decimal('950.00'))

    def test_current_balance_with_income_and_expense(self):
        from categories.models import Category
        from transactions.models import Transaction
        import datetime

        account = make_account(self.user, initial_balance='200.00')
        income_cat = Category.objects.create(name='Salary', type='income', user=self.user)
        expense_cat = Category.objects.create(name='Food', type='expense', user=self.user)
        Transaction.objects.create(
            user=self.user, account=account, category=income_cat,
            description='Salary', amount=Decimal('300.00'), type='income',
            date=datetime.date.today(),
        )
        Transaction.objects.create(
            user=self.user, account=account, category=expense_cat,
            description='Rent', amount=Decimal('100.00'), type='expense',
            date=datetime.date.today(),
        )
        # 200 + 300 - 100 = 400
        self.assertEqual(account.current_balance, Decimal('400.00'))

    def test_timestamps_auto_set(self):
        account = make_account(self.user)
        self.assertIsNotNone(account.created_at)
        self.assertIsNotNone(account.updated_at)


class AccountFormTests(TestCase):
    """Tests for the AccountForm."""

    def test_valid_form(self):
        form = AccountForm(data={
            'name': 'Nubank',
            'type': 'checking',
            'initial_balance': '1000.00',
            'description': 'Main account',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_name(self):
        form = AccountForm(data={
            'name': '',
            'type': 'checking',
            'initial_balance': '0.00',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_missing_type(self):
        form = AccountForm(data={
            'name': 'Account',
            'type': '',
            'initial_balance': '0.00',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('type', form.errors)

    def test_description_is_optional(self):
        form = AccountForm(data={
            'name': 'Wallet',
            'type': 'wallet',
            'initial_balance': '50.00',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_account_type(self):
        form = AccountForm(data={
            'name': 'Test',
            'type': 'invalid_type',
            'initial_balance': '0.00',
        })
        self.assertFalse(form.is_valid())


class AccountViewTests(TestCase):
    """Tests for Account CRUD views."""

    def setUp(self):
        self.user = make_user()
        self.other_user = make_user(email='other@test.com')
        self.client = Client()

    def _login(self):
        self.client.login(username='user@test.com', password='pass123word!')

    # --- Unauthenticated redirects ---

    def test_list_redirects_unauthenticated(self):
        response = self.client.get(reverse('accounts:list'))
        self.assertRedirects(response, '/auth/login/?next=/accounts/')

    def test_create_redirects_unauthenticated(self):
        response = self.client.get(reverse('accounts:create'))
        self.assertRedirects(response, '/auth/login/?next=/accounts/new/')

    def test_update_redirects_unauthenticated(self):
        account = make_account(self.user)
        response = self.client.get(reverse('accounts:update', args=[account.pk]))
        self.assertRedirects(
            response,
            f'/auth/login/?next=/accounts/{account.pk}/edit/',
        )

    def test_delete_redirects_unauthenticated(self):
        account = make_account(self.user)
        response = self.client.get(reverse('accounts:delete', args=[account.pk]))
        self.assertRedirects(
            response,
            f'/auth/login/?next=/accounts/{account.pk}/delete/',
        )

    # --- Authenticated: list ---

    def test_list_returns_200_for_authenticated_user(self):
        self._login()
        response = self.client.get(reverse('accounts:list'))
        self.assertEqual(response.status_code, 200)

    def test_list_shows_only_own_accounts(self):
        self._login()
        own_account = make_account(self.user, name='My Account')
        make_account(self.other_user, name='Other Account')
        response = self.client.get(reverse('accounts:list'))
        accounts = response.context['accounts']
        self.assertIn(own_account, accounts)
        self.assertNotIn(
            Account.objects.get(name='Other Account'),
            accounts,
        )

    # --- Authenticated: create ---

    def test_create_get_returns_200(self):
        self._login()
        response = self.client.get(reverse('accounts:create'))
        self.assertEqual(response.status_code, 200)

    def test_create_post_creates_account_for_user(self):
        self._login()
        response = self.client.post(reverse('accounts:create'), {
            'name': 'New Account',
            'type': 'savings',
            'initial_balance': '250.00',
            'description': '',
        })
        self.assertRedirects(response, reverse('accounts:list'))
        self.assertTrue(Account.objects.filter(name='New Account', user=self.user).exists())

    # --- Authenticated: update ---

    def test_update_get_returns_200_for_own_account(self):
        self._login()
        account = make_account(self.user)
        response = self.client.get(reverse('accounts:update', args=[account.pk]))
        self.assertEqual(response.status_code, 200)

    def test_update_post_modifies_account(self):
        self._login()
        account = make_account(self.user)
        response = self.client.post(reverse('accounts:update', args=[account.pk]), {
            'name': 'Updated Name',
            'type': 'savings',
            'initial_balance': '999.00',
        })
        self.assertRedirects(response, reverse('accounts:list'))
        account.refresh_from_db()
        self.assertEqual(account.name, 'Updated Name')

    def test_update_other_user_account_returns_404(self):
        self._login()
        other_account = make_account(self.other_user, name='Other Account')
        response = self.client.post(
            reverse('accounts:update', args=[other_account.pk]),
            {'name': 'Hacked', 'type': 'checking', 'initial_balance': '0.00'},
        )
        self.assertEqual(response.status_code, 404)

    # --- Authenticated: delete ---

    def test_delete_own_account(self):
        self._login()
        account = make_account(self.user)
        response = self.client.post(reverse('accounts:delete', args=[account.pk]))
        self.assertRedirects(response, reverse('accounts:list'))
        self.assertFalse(Account.objects.filter(pk=account.pk).exists())

    def test_delete_other_user_account_returns_404(self):
        self._login()
        other_account = make_account(self.other_user)
        response = self.client.post(reverse('accounts:delete', args=[other_account.pk]))
        self.assertEqual(response.status_code, 404)
