from django.test import TestCase

from profiles.models import Profile
from users.models import User


class ProfileSignalTests(TestCase):
    """Tests for the post_save signal that auto-creates Profile on User creation."""

    def test_profile_created_on_user_creation(self):
        user = User.objects.create_user(
            email='signal@example.com',
            password='pass123!',
            first_name='Signal',
            last_name='Test',
        )
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_profile_linked_to_correct_user(self):
        user = User.objects.create_user(
            email='linked@example.com',
            password='pass123!',
            first_name='Linked',
            last_name='Test',
        )
        profile = Profile.objects.get(user=user)
        self.assertEqual(profile.user, user)

    def test_no_duplicate_profile_on_user_save(self):
        user = User.objects.create_user(
            email='nodup@example.com',
            password='pass123!',
            first_name='NoDup',
            last_name='Test',
        )
        # Save again - should not create a second profile
        user.first_name = 'Updated'
        user.save()
        self.assertEqual(Profile.objects.filter(user=user).count(), 1)

    def test_multiple_users_each_get_own_profile(self):
        user_a = User.objects.create_user(
            email='usera@example.com',
            password='pass123!',
            first_name='A',
            last_name='Test',
        )
        user_b = User.objects.create_user(
            email='userb@example.com',
            password='pass123!',
            first_name='B',
            last_name='Test',
        )
        self.assertTrue(Profile.objects.filter(user=user_a).exists())
        self.assertTrue(Profile.objects.filter(user=user_b).exists())
        self.assertEqual(Profile.objects.count(), 2)

    def test_profile_str_returns_user_email(self):
        user = User.objects.create_user(
            email='strtest@example.com',
            password='pass123!',
            first_name='Str',
            last_name='Test',
        )
        profile = Profile.objects.get(user=user)
        self.assertEqual(str(profile), 'strtest@example.com')
