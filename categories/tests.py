from django.test import Client, TestCase
from django.urls import reverse

from categories.forms import CategoryForm
from categories.models import Category
from users.models import User


def make_user(email='user@test.com', password='pass123word!'):
    return User.objects.create_user(
        email=email,
        password=password,
        first_name='Test',
        last_name='User',
    )


def make_category(user, name='Food', category_type='expense', color='#ff0000'):
    return Category.objects.create(
        user=user,
        name=name,
        type=category_type,
        color=color,
    )


class CategoryModelTests(TestCase):
    """Tests for the Category model."""

    def setUp(self):
        self.user = make_user()

    def test_category_creation(self):
        category = make_category(self.user)
        self.assertEqual(category.name, 'Food')
        self.assertEqual(category.type, 'expense')
        self.assertEqual(category.color, '#ff0000')
        self.assertEqual(category.user, self.user)

    def test_global_category_has_no_user(self):
        category = Category.objects.create(
            user=None,
            name='Global Category',
            type='income',
            color='#334155',
        )
        self.assertIsNone(category.user)

    def test_str_representation(self):
        category = make_category(self.user, name='Salary', category_type='income')
        self.assertIn('Salary', str(category))

    def test_default_color(self):
        category = Category.objects.create(
            user=self.user,
            name='No Color',
            type='expense',
        )
        self.assertEqual(category.color, '#334155')

    def test_timestamps_auto_set(self):
        category = make_category(self.user)
        self.assertIsNotNone(category.created_at)
        self.assertIsNotNone(category.updated_at)

    def test_ordering_by_name(self):
        make_category(self.user, name='Zzz')
        make_category(self.user, name='Aaa')
        categories = list(Category.objects.filter(user=self.user))
        self.assertEqual(categories[0].name, 'Aaa')
        self.assertEqual(categories[1].name, 'Zzz')


class CategoryFormTests(TestCase):
    """Tests for the CategoryForm."""

    def test_valid_form(self):
        form = CategoryForm(data={
            'name': 'Transportation',
            'type': 'expense',
            'color': '#123456',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_name(self):
        form = CategoryForm(data={
            'name': '',
            'type': 'expense',
            'color': '#000000',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_missing_type(self):
        form = CategoryForm(data={
            'name': 'Test',
            'type': '',
            'color': '#000000',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('type', form.errors)

    def test_invalid_type(self):
        form = CategoryForm(data={
            'name': 'Test',
            'type': 'invalid',
            'color': '#000000',
        })
        self.assertFalse(form.is_valid())

    def test_income_type_valid(self):
        form = CategoryForm(data={
            'name': 'Salary',
            'type': 'income',
            'color': '#00ff00',
        })
        self.assertTrue(form.is_valid(), form.errors)


class CategoryViewTests(TestCase):
    """Tests for Category CRUD views."""

    def setUp(self):
        self.user = make_user()
        self.other_user = make_user(email='other@test.com')
        self.client = Client()

    def _login(self):
        self.client.login(username='user@test.com', password='pass123word!')

    # --- Unauthenticated redirects ---

    def test_list_redirects_unauthenticated(self):
        response = self.client.get(reverse('categories:list'))
        self.assertRedirects(response, '/auth/login/?next=/categories/')

    def test_create_redirects_unauthenticated(self):
        response = self.client.get(reverse('categories:create'))
        self.assertRedirects(response, '/auth/login/?next=/categories/new/')

    def test_update_redirects_unauthenticated(self):
        category = make_category(self.user)
        response = self.client.get(reverse('categories:update', args=[category.pk]))
        self.assertRedirects(
            response,
            f'/auth/login/?next=/categories/{category.pk}/edit/',
        )

    def test_delete_redirects_unauthenticated(self):
        category = make_category(self.user)
        response = self.client.get(reverse('categories:delete', args=[category.pk]))
        self.assertRedirects(
            response,
            f'/auth/login/?next=/categories/{category.pk}/delete/',
        )

    # --- Authenticated: list ---

    def test_list_returns_200_for_authenticated_user(self):
        self._login()
        response = self.client.get(reverse('categories:list'))
        self.assertEqual(response.status_code, 200)

    def test_list_shows_own_and_global_categories(self):
        self._login()
        own = make_category(self.user, name='My Category')
        global_cat = Category.objects.create(name='Global', type='expense', user=None)
        other_cat = make_category(self.other_user, name='Other Category')
        response = self.client.get(reverse('categories:list'))
        categories = list(response.context['categories'])
        self.assertIn(own, categories)
        self.assertIn(global_cat, categories)
        self.assertNotIn(other_cat, categories)

    # --- Authenticated: create ---

    def test_create_get_returns_200(self):
        self._login()
        response = self.client.get(reverse('categories:create'))
        self.assertEqual(response.status_code, 200)

    def test_create_post_creates_category_for_user(self):
        self._login()
        response = self.client.post(reverse('categories:create'), {
            'name': 'New Category',
            'type': 'income',
            'color': '#abcdef',
        })
        self.assertRedirects(response, reverse('categories:list'))
        self.assertTrue(
            Category.objects.filter(name='New Category', user=self.user).exists()
        )

    # --- Authenticated: update ---

    def test_update_get_returns_200_for_own_category(self):
        self._login()
        category = make_category(self.user)
        response = self.client.get(reverse('categories:update', args=[category.pk]))
        self.assertEqual(response.status_code, 200)

    def test_update_post_modifies_category(self):
        self._login()
        category = make_category(self.user)
        response = self.client.post(
            reverse('categories:update', args=[category.pk]),
            {'name': 'Updated Name', 'type': 'income', 'color': '#ffffff'},
        )
        self.assertRedirects(response, reverse('categories:list'))
        category.refresh_from_db()
        self.assertEqual(category.name, 'Updated Name')

    def test_update_other_user_category_returns_404(self):
        self._login()
        other_category = make_category(self.other_user, name='Other Cat')
        response = self.client.post(
            reverse('categories:update', args=[other_category.pk]),
            {'name': 'Hacked', 'type': 'expense', 'color': '#000000'},
        )
        self.assertEqual(response.status_code, 404)

    # --- Authenticated: delete ---

    def test_delete_own_category(self):
        self._login()
        category = make_category(self.user)
        response = self.client.post(reverse('categories:delete', args=[category.pk]))
        self.assertRedirects(response, reverse('categories:list'))
        self.assertFalse(Category.objects.filter(pk=category.pk).exists())

    def test_delete_other_user_category_returns_404(self):
        self._login()
        other_category = make_category(self.other_user)
        response = self.client.post(reverse('categories:delete', args=[other_category.pk]))
        self.assertEqual(response.status_code, 404)

    def test_cannot_delete_global_category(self):
        """Global categories (user=None) cannot be deleted by any user."""
        self._login()
        global_cat = Category.objects.create(name='Global', type='expense', user=None)
        response = self.client.post(reverse('categories:delete', args=[global_cat.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Category.objects.filter(pk=global_cat.pk).exists())
