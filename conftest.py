import pytest
from django.test import Client

from users.models import User


@pytest.fixture
def user(db):
    """Create a regular test user."""
    return User.objects.create_user(
        email='test@test.com',
        password='pass123word!',
        first_name='Test',
        last_name='User',
    )


@pytest.fixture
def other_user(db):
    """Create a second user for isolation tests."""
    return User.objects.create_user(
        email='other@test.com',
        password='pass123word!',
        first_name='Other',
        last_name='User',
    )


@pytest.fixture
def authenticated_client(user):
    """Return a Django test client logged in as the test user."""
    client = Client()
    client.login(username='test@test.com', password='pass123word!')
    return client
