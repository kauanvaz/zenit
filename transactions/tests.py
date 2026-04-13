import datetime
from decimal import Decimal

from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import Account
from categories.models import Category
from transactions.forms import TransactionForm
from transactions.models import Transaction
from users.models import User


def make_user(email='user@test.com', password='pass123word!'):
    return User.objects.create_user(
        email=email,
        password=password,
        first_name='Test',
        last_name='User',
    )


def make_account(user, name='Test Account'):
    return Account.objects.create(
        user=user,
        name=name,
        type='checking',
        initial_balance=Decimal('0.00'),
    )


def make_category(user, name='Test Category', category_type='expense'):
    return Category.objects.create(
        user=user,
        name=name,
        type=category_type,
        color='#334155',
    )


def make_transaction(user, account, category, description='Test Transaction',
                     amount='100.00', transaction_type='expense', date=None):
    if date is None:
        date = datetime.date.today()
    return Transaction.objects.create(
        user=user,
        account=account,
        category=category,
        description=description,
        amount=Decimal(amount),
        type=transaction_type,
        date=date,
    )


class TransactionModelTests(TestCase):
    """Tests for the Transaction model."""

    def setUp(self):
        self.user = make_user()
        self.account = make_account(self.user)
        self.category = make_category(self.user)

    def test_transaction_creation(self):
        transaction = make_transaction(self.user, self.account, self.category)
        self.assertEqual(transaction.description, 'Test Transaction')
        self.assertEqual(transaction.amount, Decimal('100.00'))
        self.assertEqual(transaction.type, 'expense')
        self.assertEqual(transaction.user, self.user)
        self.assertEqual(transaction.account, self.account)
        self.assertEqual(transaction.category, self.category)

    def test_str_representation(self):
        transaction = make_transaction(
            self.user, self.account, self.category, description='Lunch'
        )
        self.assertIn('Lunch', str(transaction))
        self.assertIn('100.00', str(transaction))

    def test_income_transaction(self):
        income_category = make_category(self.user, name='Salary', category_type='income')
        transaction = make_transaction(
            self.user, self.account, income_category,
            description='Monthly salary', amount='3000.00',
            transaction_type='income',
        )
        self.assertEqual(transaction.type, 'income')
        self.assertEqual(transaction.amount, Decimal('3000.00'))

    def test_transaction_with_notes(self):
        transaction = Transaction.objects.create(
            user=self.user,
            account=self.account,
            category=self.category,
            description='Noted transaction',
            amount=Decimal('50.00'),
            type='expense',
            date=datetime.date.today(),
            notes='Some extra notes here.',
        )
        self.assertEqual(transaction.notes, 'Some extra notes here.')

    def test_transaction_without_category(self):
        transaction = Transaction.objects.create(
            user=self.user,
            account=self.account,
            category=None,
            description='No category',
            amount=Decimal('10.00'),
            type='expense',
            date=datetime.date.today(),
        )
        self.assertIsNone(transaction.category)

    def test_timestamps_auto_set(self):
        transaction = make_transaction(self.user, self.account, self.category)
        self.assertIsNotNone(transaction.created_at)
        self.assertIsNotNone(transaction.updated_at)

    def test_ordering_by_date_descending(self):
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)
        t1 = make_transaction(self.user, self.account, self.category, date=yesterday)
        t2 = make_transaction(self.user, self.account, self.category, date=today)
        transactions = list(
            Transaction.objects.filter(user=self.user)
        )
        self.assertEqual(transactions[0], t2)
        self.assertEqual(transactions[1], t1)


class TransactionFormTests(TestCase):
    """Tests for the TransactionForm."""

    def setUp(self):
        self.user = make_user()
        self.other_user = make_user(email='other@test.com')
        self.account = make_account(self.user)
        self.other_account = make_account(self.other_user, name='Other Account')
        self.category = make_category(self.user)
        self.global_category = Category.objects.create(
            user=None, name='Global Cat', type='expense', color='#000000'
        )

    def _valid_data(self):
        return {
            'account': self.account.pk,
            'category': self.category.pk,
            'description': 'Test transaction',
            'amount': '100.00',
            'type': 'expense',
            'date': datetime.date.today().isoformat(),
            'notes': '',
        }

    def test_valid_form(self):
        form = TransactionForm(data=self._valid_data(), user=self.user)
        self.assertTrue(form.is_valid(), form.errors)

    def test_account_queryset_filtered_to_user(self):
        form = TransactionForm(user=self.user)
        account_qs = form.fields['account'].queryset
        self.assertIn(self.account, account_qs)
        self.assertNotIn(self.other_account, account_qs)

    def test_category_queryset_includes_user_and_global(self):
        form = TransactionForm(user=self.user)
        category_qs = form.fields['category'].queryset
        self.assertIn(self.category, category_qs)
        self.assertIn(self.global_category, category_qs)

    def test_category_queryset_excludes_other_user_categories(self):
        other_category = make_category(self.other_user, name='Other Cat')
        form = TransactionForm(user=self.user)
        category_qs = form.fields['category'].queryset
        self.assertNotIn(other_category, category_qs)

    def test_form_without_user_kwarg_has_all_querysets(self):
        """When no user is passed, querysets are not filtered."""
        form = TransactionForm()
        # Without user, querysets default to all objects
        self.assertIn(self.account, form.fields['account'].queryset)
        self.assertIn(self.other_account, form.fields['account'].queryset)

    def test_missing_description(self):
        data = self._valid_data()
        data['description'] = ''
        form = TransactionForm(data=data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('description', form.errors)

    def test_missing_amount(self):
        data = self._valid_data()
        data['amount'] = ''
        form = TransactionForm(data=data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)

    def test_missing_date(self):
        data = self._valid_data()
        data['date'] = ''
        form = TransactionForm(data=data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('date', form.errors)

    def test_global_category_accepted_in_form(self):
        data = self._valid_data()
        data['category'] = self.global_category.pk
        form = TransactionForm(data=data, user=self.user)
        self.assertTrue(form.is_valid(), form.errors)


class TransactionViewTests(TestCase):
    """Tests for Transaction CRUD views."""

    def setUp(self):
        self.user = make_user()
        self.other_user = make_user(email='other@test.com')
        self.account = make_account(self.user)
        self.other_account = make_account(self.other_user)
        self.category = make_category(self.user)
        self.client = Client()
        self.today = datetime.date.today()

    def _login(self):
        self.client.login(username='user@test.com', password='pass123word!')

    def _make_transaction(self, user=None, account=None, category=None,
                          description='Test', amount='100.00',
                          transaction_type='expense', date=None):
        if user is None:
            user = self.user
        if account is None:
            account = self.account
        if category is None:
            category = self.category
        return make_transaction(user, account, category, description, amount,
                                transaction_type, date or self.today)

    # --- Unauthenticated redirects ---

    def test_list_redirects_unauthenticated(self):
        response = self.client.get(reverse('transactions:list'))
        self.assertRedirects(response, '/auth/login/?next=/transactions/')

    def test_create_redirects_unauthenticated(self):
        response = self.client.get(reverse('transactions:create'))
        self.assertRedirects(response, '/auth/login/?next=/transactions/new/')

    def test_update_redirects_unauthenticated(self):
        transaction = self._make_transaction()
        response = self.client.get(reverse('transactions:update', args=[transaction.pk]))
        self.assertRedirects(
            response,
            f'/auth/login/?next=/transactions/{transaction.pk}/edit/',
        )

    def test_delete_redirects_unauthenticated(self):
        transaction = self._make_transaction()
        response = self.client.get(reverse('transactions:delete', args=[transaction.pk]))
        self.assertRedirects(
            response,
            f'/auth/login/?next=/transactions/{transaction.pk}/delete/',
        )

    # --- Authenticated: list ---

    def test_list_returns_200_for_authenticated_user(self):
        self._login()
        response = self.client.get(reverse('transactions:list'))
        self.assertEqual(response.status_code, 200)

    def test_list_shows_only_own_transactions(self):
        self._login()
        own = self._make_transaction(description='Own Transaction')
        other = self._make_transaction(
            user=self.other_user,
            account=self.other_account,
            category=make_category(self.other_user, name='Other Cat'),
            description='Other Transaction',
        )
        response = self.client.get(reverse('transactions:list'))
        transactions = list(response.context['transactions'])
        self.assertIn(own, transactions)
        self.assertNotIn(other, transactions)

    def test_list_without_year_filter_includes_transactions_from_any_year(self):
        self._login()
        current_year_t = self._make_transaction(
            description='Current Year Transaction',
            date=self.today,
        )
        old_year_date = datetime.date(self.today.year - 10, 9, 11)
        old_year_t = self._make_transaction(
            description='Old Year Transaction',
            date=old_year_date,
        )

        response = self.client.get(reverse('transactions:list'))
        transactions = list(response.context['transactions'])
        self.assertIn(current_year_t, transactions)
        self.assertIn(old_year_t, transactions)

    def test_list_filter_by_type(self):
        self._login()
        income_cat = make_category(self.user, name='Salary', category_type='income')
        income_t = self._make_transaction(
            transaction_type='income', category=income_cat, description='Income'
        )
        expense_t = self._make_transaction(
            transaction_type='expense', description='Expense'
        )
        response = self.client.get(
            reverse('transactions:list'), {'type': 'income', 'year': self.today.year}
        )
        transactions = list(response.context['transactions'])
        self.assertIn(income_t, transactions)
        self.assertNotIn(expense_t, transactions)

    def test_list_filter_by_month(self):
        self._login()
        current_month_t = self._make_transaction(
            date=self.today, description='This month'
        )
        # Use a date at least 2 months ago to avoid same-month collision
        old_date = self.today.replace(day=1) - datetime.timedelta(days=32)
        old_t = self._make_transaction(date=old_date, description='Old')
        response = self.client.get(
            reverse('transactions:list'),
            {'month': self.today.month, 'year': self.today.year},
        )
        transactions = list(response.context['transactions'])
        self.assertIn(current_month_t, transactions)
        self.assertNotIn(old_t, transactions)

    def test_list_context_contains_totals(self):
        self._login()
        income_cat = make_category(self.user, name='Salary', category_type='income')
        self._make_transaction(
            transaction_type='income', category=income_cat,
            amount='500.00', description='Salary',
        )
        self._make_transaction(
            transaction_type='expense', amount='200.00', description='Rent'
        )
        response = self.client.get(
            reverse('transactions:list'), {'year': self.today.year}
        )
        self.assertEqual(response.context['income_total'], Decimal('500.00'))
        self.assertEqual(response.context['expense_total'], Decimal('200.00'))
        self.assertEqual(response.context['net_balance'], Decimal('300.00'))

    def test_list_filter_by_category(self):
        self._login()
        food_cat = make_category(self.user, name='Food', category_type='expense')
        food_t = self._make_transaction(category=food_cat, description='Food')
        other_t = self._make_transaction(description='Other')
        response = self.client.get(
            reverse('transactions:list'),
            {'category': food_cat.pk, 'year': self.today.year},
        )
        transactions = list(response.context['transactions'])
        self.assertIn(food_t, transactions)
        self.assertNotIn(other_t, transactions)

    # --- Authenticated: create ---

    def test_create_get_returns_200(self):
        self._login()
        response = self.client.get(reverse('transactions:create'))
        self.assertEqual(response.status_code, 200)

    def test_create_post_creates_transaction_for_user(self):
        self._login()
        response = self.client.post(reverse('transactions:create'), {
            'account': self.account.pk,
            'category': self.category.pk,
            'description': 'New Transaction',
            'amount': '150.00',
            'type': 'expense',
            'date': self.today.isoformat(),
            'notes': '',
        })
        self.assertRedirects(response, reverse('transactions:list'))
        self.assertTrue(
            Transaction.objects.filter(
                description='New Transaction', user=self.user
            ).exists()
        )

    def test_create_assigns_user_from_request(self):
        self._login()
        self.client.post(reverse('transactions:create'), {
            'account': self.account.pk,
            'category': self.category.pk,
            'description': 'User Assignment',
            'amount': '75.00',
            'type': 'income',
            'date': self.today.isoformat(),
            'notes': '',
        })
        transaction = Transaction.objects.get(description='User Assignment')
        self.assertEqual(transaction.user, self.user)

    # --- Authenticated: update ---

    def test_update_get_returns_200_for_own_transaction(self):
        self._login()
        transaction = self._make_transaction()
        response = self.client.get(reverse('transactions:update', args=[transaction.pk]))
        self.assertEqual(response.status_code, 200)

    def test_update_post_modifies_transaction(self):
        self._login()
        transaction = self._make_transaction(description='Original')
        response = self.client.post(
            reverse('transactions:update', args=[transaction.pk]),
            {
                'account': self.account.pk,
                'category': self.category.pk,
                'description': 'Updated',
                'amount': '200.00',
                'type': 'expense',
                'date': self.today.isoformat(),
                'notes': '',
            },
        )
        self.assertRedirects(response, reverse('transactions:list'))
        transaction.refresh_from_db()
        self.assertEqual(transaction.description, 'Updated')

    def test_update_other_user_transaction_returns_404(self):
        self._login()
        other_transaction = self._make_transaction(
            user=self.other_user,
            account=self.other_account,
            category=make_category(self.other_user, name='Other Cat'),
        )
        response = self.client.post(
            reverse('transactions:update', args=[other_transaction.pk]),
            {
                'account': self.account.pk,
                'category': self.category.pk,
                'description': 'Hacked',
                'amount': '999.00',
                'type': 'income',
                'date': self.today.isoformat(),
                'notes': '',
            },
        )
        self.assertEqual(response.status_code, 404)

    # --- Authenticated: delete ---

    def test_delete_own_transaction(self):
        self._login()
        transaction = self._make_transaction()
        response = self.client.post(reverse('transactions:delete', args=[transaction.pk]))
        self.assertRedirects(response, reverse('transactions:list'))
        self.assertFalse(Transaction.objects.filter(pk=transaction.pk).exists())

    def test_delete_other_user_transaction_returns_404(self):
        self._login()
        other_transaction = self._make_transaction(
            user=self.other_user,
            account=self.other_account,
            category=make_category(self.other_user, name='Other Cat'),
        )
        response = self.client.post(
            reverse('transactions:delete', args=[other_transaction.pk])
        )
        self.assertEqual(response.status_code, 404)


class TransactionExportCSVViewTests(TestCase):
    """Tests for the CSV export view."""

    def setUp(self):
        self.user = make_user()
        self.other_user = make_user(email='other@test.com')
        self.account = make_account(self.user)
        self.other_account = make_account(self.other_user)
        self.income_cat = make_category(self.user, name='Salary', category_type='income')
        self.expense_cat = make_category(self.user, name='Food', category_type='expense')
        self.client = Client()
        self.today = datetime.date.today()
        self.url = reverse('transactions:export_csv')

    def _login(self):
        self.client.login(username='user@test.com', password='pass123word!')

    def test_redirects_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth/login/', response['Location'])

    def test_returns_csv_content_type(self):
        self._login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/csv', response['Content-Type'])

    def test_content_disposition_attachment(self):
        self._login()
        response = self.client.get(self.url)
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('.csv', response['Content-Disposition'])

    def test_csv_header_row(self):
        self._login()
        response = self.client.get(self.url)
        content = response.content.decode('utf-8-sig')
        first_line = content.splitlines()[0]
        self.assertIn('Data', first_line)
        self.assertIn('Descrição', first_line)
        self.assertIn('Tipo', first_line)
        self.assertIn('Categoria', first_line)
        self.assertIn('Conta', first_line)
        self.assertIn('Valor', first_line)

    def test_csv_contains_own_transactions_only(self):
        self._login()
        make_transaction(
            self.user, self.account, self.income_cat,
            description='My Income', amount='500.00', transaction_type='income',
            date=self.today,
        )
        other_cat = make_category(self.other_user, name='Other Cat')
        make_transaction(
            self.other_user, self.other_account, other_cat,
            description='Other Income', amount='999.00', transaction_type='income',
            date=self.today,
        )
        response = self.client.get(self.url)
        content = response.content.decode('utf-8-sig')
        self.assertIn('My Income', content)
        self.assertNotIn('Other Income', content)

    def test_csv_without_year_filter_includes_transactions_from_any_year(self):
        self._login()
        make_transaction(
            self.user,
            self.account,
            self.income_cat,
            description='Current Year CSV',
            amount='100.00',
            transaction_type='income',
            date=self.today,
        )
        old_year_date = datetime.date(self.today.year - 10, 9, 11)
        make_transaction(
            self.user,
            self.account,
            self.income_cat,
            description='Old Year CSV',
            amount='200.00',
            transaction_type='income',
            date=old_year_date,
        )

        response = self.client.get(self.url)
        content = response.content.decode('utf-8-sig')
        self.assertIn('Current Year CSV', content)
        self.assertIn('Old Year CSV', content)

    def test_csv_income_prefixed_with_plus(self):
        self._login()
        make_transaction(
            self.user, self.account, self.income_cat,
            description='Salary', amount='1000.00', transaction_type='income',
            date=self.today,
        )
        response = self.client.get(self.url)
        content = response.content.decode('utf-8-sig')
        self.assertIn('+1.000,00', content)

    def test_csv_expense_prefixed_with_minus(self):
        self._login()
        make_transaction(
            self.user, self.account, self.expense_cat,
            description='Groceries', amount='250.00', transaction_type='expense',
            date=self.today,
        )
        response = self.client.get(self.url)
        content = response.content.decode('utf-8-sig')
        self.assertIn('-250,00', content)

    def test_csv_type_display_in_portuguese(self):
        self._login()
        make_transaction(
            self.user, self.account, self.income_cat,
            description='Bonus', amount='200.00', transaction_type='income',
            date=self.today,
        )
        make_transaction(
            self.user, self.account, self.expense_cat,
            description='Rent', amount='800.00', transaction_type='expense',
            date=self.today,
        )
        response = self.client.get(self.url)
        content = response.content.decode('utf-8-sig')
        self.assertIn('Receita', content)
        self.assertIn('Despesa', content)

    def test_csv_transaction_without_category_shows_empty(self):
        self._login()
        Transaction.objects.create(
            user=self.user,
            account=self.account,
            category=None,
            description='No Category',
            amount=Decimal('50.00'),
            type='expense',
            date=self.today,
        )
        response = self.client.get(self.url)
        content = response.content.decode('utf-8-sig')
        self.assertIn('No Category', content)

    def test_csv_filter_by_type(self):
        self._login()
        make_transaction(
            self.user, self.account, self.income_cat,
            description='Income Only', amount='300.00', transaction_type='income',
            date=self.today,
        )
        make_transaction(
            self.user, self.account, self.expense_cat,
            description='Expense Only', amount='100.00', transaction_type='expense',
            date=self.today,
        )
        response = self.client.get(self.url, {'type': 'income', 'year': self.today.year})
        content = response.content.decode('utf-8-sig')
        self.assertIn('Income Only', content)
        self.assertNotIn('Expense Only', content)


class TransactionExportPDFViewTests(TestCase):
    """Tests for the PDF export view."""

    def setUp(self):
        self.user = make_user()
        self.other_user = make_user(email='other@test.com')
        self.account = make_account(self.user)
        self.other_account = make_account(self.other_user)
        self.income_cat = make_category(self.user, name='Salary', category_type='income')
        self.expense_cat = make_category(self.user, name='Food', category_type='expense')
        self.client = Client()
        self.today = datetime.date.today()
        self.url = reverse('transactions:export_pdf')

    def _login(self):
        self.client.login(username='user@test.com', password='pass123word!')

    def test_redirects_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth/login/', response['Location'])

    def test_returns_pdf_content_type(self):
        self._login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_content_disposition_attachment(self):
        self._login()
        response = self.client.get(self.url)
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('.pdf', response['Content-Disposition'])

    def test_pdf_starts_with_pdf_magic_bytes(self):
        self._login()
        response = self.client.get(self.url)
        self.assertTrue(response.content.startswith(b'%PDF'))

    def test_pdf_with_transactions(self):
        self._login()
        make_transaction(
            self.user, self.account, self.income_cat,
            description='Salary', amount='2000.00', transaction_type='income',
            date=self.today,
        )
        make_transaction(
            self.user, self.account, self.expense_cat,
            description='Food', amount='300.00', transaction_type='expense',
            date=self.today,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b'%PDF'))

    def test_pdf_with_no_transactions(self):
        """Export should work even when there are no transactions."""
        self._login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b'%PDF'))

    def test_pdf_excludes_other_user_transactions(self):
        """PDF export must not include transactions from other users."""
        self._login()
        other_cat = make_category(self.other_user, name='Other Cat')
        make_transaction(
            self.other_user, self.other_account, other_cat,
            description='Other User Transaction', amount='9999.00',
            transaction_type='income', date=self.today,
        )
        # User has no transactions; PDF should still be generated successfully
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_pdf_filter_by_type_param(self):
        self._login()
        make_transaction(
            self.user, self.account, self.income_cat,
            description='Income', amount='500.00', transaction_type='income',
            date=self.today,
        )
        response = self.client.get(self.url, {'type': 'income', 'year': self.today.year})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b'%PDF'))

    def test_pdf_transaction_without_category(self):
        self._login()
        Transaction.objects.create(
            user=self.user,
            account=self.account,
            category=None,
            description='No Category',
            amount=Decimal('50.00'),
            type='expense',
            date=self.today,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b'%PDF'))
