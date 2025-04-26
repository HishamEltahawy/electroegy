from django.test import TestCase
from django.contrib.auth.models import User
from .models import Profile
from rest_framework.test import APITestCase
from rest_framework import status

class ProfileModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')

    def test_profile_creation(self):
        """Test that a Profile is automatically created when a User is created."""
        self.assertTrue(hasattr(self.user, 'profile'))

    def test_set_two_factor_code(self):
        """Test setting a two-factor authentication code."""
        self.user.profile.set_two_factor_code('123456')
        self.assertIsNotNone(self.user.profile.two_factor_code)

    def test_verify_two_factor_code(self):
        """Test verifying a two-factor authentication code."""
        self.user.profile.set_two_factor_code('123456')
        self.assertTrue(self.user.profile.verify_two_factor_code('123456'))
        self.assertFalse(self.user.profile.verify_two_factor_code('654321'))


class UserAuthenticationTests(APITestCase):

    def setUp(self):
        self.register_url = '/api/accounts/register/'
        self.login_url = '/api/token/'  # Assuming JWT login endpoint
        self.user_data = {
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'testuser@example.com',
            'password': 'testpassword',
        }

    def test_user_registration(self):
        """Test user registration endpoint."""
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('details', response.data)

    def test_user_login(self):
        """Test user login endpoint."""
        # Register the user first
        self.client.post(self.register_url, self.user_data)

        # Attempt to log in
        login_data = {
            'username': self.user_data['username'],
            'password': self.user_data['password'],
        }
        response = self.client.post(self.login_url, login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_2fa_verification(self):
        """Test 2FA verification endpoint."""
        # Register the user and enable 2FA
        self.client.post(self.register_url, self.user_data)
        user = User.objects.get(username=self.user_data['username'])
        user.profile.two_factor_enabled = True
        user.profile.set_two_factor_code('123456')

        # Verify the 2FA code
        verify_url = '/api/accounts/2fa/verify/'
        response = self.client.post(verify_url, {'code': '123456'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
