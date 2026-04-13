import pytest
from django.test import Client, TestCase
from django.urls import reverse

from users.forms import CustomAuthenticationForm, RegisterForm
from users.models import User


class UserModelTests(TestCase):
    """Tests for the custom User model."""

    def test_create_user(self):
        user = User.objects.create_user(
            email='alice@example.com',
            password='securepass!1',
            first_name='Alice',
            last_name='Smith',
        )
        self.assertEqual(user.email, 'alice@example.com')
        self.assertEqual(user.first_name, 'Alice')
        self.assertEqual(user.last_name, 'Smith')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertTrue(user.check_password('securepass!1'))

    def test_create_user_requires_email(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email='', password='securepass!1')

    def test_create_superuser(self):
        superuser = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass!1',
            first_name='Admin',
            last_name='User',
        )
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)

    def test_create_superuser_requires_is_staff(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email='admin@example.com',
                password='adminpass!1',
                is_staff=False,
            )

    def test_create_superuser_requires_is_superuser(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email='admin@example.com',
                password='adminpass!1',
                is_superuser=False,
            )

    def test_email_uniqueness(self):
        User.objects.create_user(
            email='unique@example.com',
            password='pass123!',
            first_name='A',
            last_name='B',
        )
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                email='unique@example.com',
                password='other123!',
                first_name='C',
                last_name='D',
            )

    def test_get_full_name(self):
        user = User.objects.create_user(
            email='full@example.com',
            password='pass!',
            first_name='John',
            last_name='Doe',
        )
        self.assertEqual(user.get_full_name(), 'John Doe')

    def test_get_short_name(self):
        user = User.objects.create_user(
            email='short@example.com',
            password='pass!',
            first_name='Jane',
            last_name='Doe',
        )
        self.assertEqual(user.get_short_name(), 'Jane')

    def test_str_returns_email(self):
        user = User.objects.create_user(
            email='str@example.com',
            password='pass!',
            first_name='X',
            last_name='Y',
        )
        self.assertEqual(str(user), 'str@example.com')

    def test_username_field_is_email(self):
        self.assertEqual(User.USERNAME_FIELD, 'email')

    def test_required_fields(self):
        self.assertIn('first_name', User.REQUIRED_FIELDS)
        self.assertIn('last_name', User.REQUIRED_FIELDS)

    def test_created_at_and_updated_at_set(self):
        user = User.objects.create_user(
            email='timestamps@example.com',
            password='pass!',
            first_name='T',
            last_name='S',
        )
        self.assertIsNotNone(user.created_at)
        self.assertIsNotNone(user.updated_at)


class RegisterFormTests(TestCase):
    """Tests for the RegisterForm."""

    def _valid_data(self, email='new@example.com'):
        return {
            'first_name': 'Alice',
            'last_name': 'Smith',
            'email': email,
            'password1': 'Str0ngP@ssword',
            'password2': 'Str0ngP@ssword',
        }

    def test_valid_form(self):
        form = RegisterForm(data=self._valid_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_duplicate_email_raises_validation_error(self):
        User.objects.create_user(
            email='existing@example.com',
            password='Str0ngP@ssword',
            first_name='Existing',
            last_name='User',
        )
        form = RegisterForm(data=self._valid_data(email='existing@example.com'))
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_duplicate_email_case_insensitive(self):
        User.objects.create_user(
            email='CaseSensitive@example.com',
            password='Str0ngP@ssword',
            first_name='Case',
            last_name='User',
        )
        form = RegisterForm(data=self._valid_data(email='casesensitive@example.com'))
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_missing_first_name(self):
        data = self._valid_data()
        data['first_name'] = ''
        form = RegisterForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('first_name', form.errors)

    def test_password_mismatch(self):
        data = self._valid_data()
        data['password2'] = 'DifferentPass123!'
        form = RegisterForm(data=data)
        self.assertFalse(form.is_valid())


class CustomAuthenticationFormTests(TestCase):
    """Tests for the CustomAuthenticationForm."""

    def test_username_field_is_email_field(self):
        from django import forms
        form = CustomAuthenticationForm()
        self.assertIsInstance(form.fields['username'], forms.EmailField)

    def test_label_is_email(self):
        form = CustomAuthenticationForm()
        self.assertEqual(form.fields['username'].label, 'E-mail')


class RegisterViewTests(TestCase):
    """Tests for the RegisterView."""

    def test_get_register_page_returns_200(self):
        client = Client()
        response = client.get(reverse('users:register'))
        self.assertEqual(response.status_code, 200)

    def test_get_uses_correct_template(self):
        client = Client()
        response = client.get(reverse('users:register'))
        self.assertTemplateUsed(response, 'auth/register.html')

    def test_post_valid_data_creates_user_and_redirects_to_dashboard(self):
        client = Client()
        response = client.post(reverse('users:register'), {
            'first_name': 'New',
            'last_name': 'User',
            'email': 'newuser@example.com',
            'password1': 'Str0ngP@ssword',
            'password2': 'Str0ngP@ssword',
        })
        self.assertRedirects(response, reverse('dashboard'))
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())

    def test_post_valid_data_logs_user_in(self):
        client = Client()
        client.post(reverse('users:register'), {
            'first_name': 'New',
            'last_name': 'User',
            'email': 'loggedin@example.com',
            'password1': 'Str0ngP@ssword',
            'password2': 'Str0ngP@ssword',
        })
        user = User.objects.get(email='loggedin@example.com')
        response = client.get(reverse('dashboard'))
        # If the user is authenticated, we should not be redirected to login
        self.assertNotEqual(response.status_code, 302)

    def test_post_duplicate_email_shows_form_error(self):
        User.objects.create_user(
            email='taken@example.com',
            password='Str0ngP@ssword',
            first_name='Taken',
            last_name='User',
        )
        client = Client()
        response = client.post(reverse('users:register'), {
            'first_name': 'New',
            'last_name': 'User',
            'email': 'taken@example.com',
            'password1': 'Str0ngP@ssword',
            'password2': 'Str0ngP@ssword',
        })
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertIn('email', form.errors)
        self.assertIn('Este e-mail já está cadastrado.', form.errors['email'])
