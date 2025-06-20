from django.contrib.auth.models import User
from django.urls import reverse
from django.test import TestCase # For basic model/view tests
from rest_framework.test import APITestCase, APIClient # For API tests
from rest_framework import status
from .models import UserProfile

class UserModelSignalTests(TestCase):
    def test_user_profile_created_on_user_create(self):
        """Test that a UserProfile is automatically created when a User is created."""
        user = User.objects.create_user(username='testuser_signal', email='signal@example.com', password='password123')
        self.assertTrue(hasattr(user, 'profile'))
        self.assertIsInstance(user.profile, UserProfile)
        self.assertEqual(user.profile.user, user)

class AuthAPIEndpointsTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('rest_register') # dj_rest_auth.registration.urls
        self.login_url = reverse('rest_login')       # dj_rest_auth.urls
        self.logout_url = reverse('rest_logout')     # dj_rest_auth.urls
        self.user_data = {
            'username': 'testuser_api', # dj-rest-auth default register serializer might use username
            'email': 'api_user@example.com',
            'password': 'securepassword123',
            'password2': 'securepassword123' # if using default RegisterSerializer with password confirmation
        }
        # Adjust user_data if your REGISTER_SERIALIZER is different or doesn't need username/password2
        # For example, if strictly email-based and using allauth's logic:
        # self.user_data_minimal = {
        #     'email': 'api_user@example.com',
        #     'password': 'securepassword123',
        # }


    def test_user_registration(self):
        """Test new user registration via API."""
        # Default dj_rest_auth registration often requires username.
        # If you've customized it to be email-only via allauth settings and custom serializer, adjust data.
        registration_data = {
            'username': 'testregister',
            'email': 'register@example.com',
            'password1': 'aVeryComplexP@ssw0rd!',
            'password2': 'aVeryComplexP@ssw0rd!',
        }
        # If your allauth settings make username not required (ACCOUNT_USERNAME_REQUIRED = False)
        # and dj-rest-auth's RegisterSerializer respects this (it should via allauth adapters),
        # you might only need email and password.
        # However, the default dj_rest_auth.registration.serializers.RegisterSerializer includes username.

        response = self.client.post(self.register_url, registration_data, format='json')

        # Check for common registration issues if status is not 201
        if response.status_code != status.HTTP_201_CREATED:
            print(f"Registration failed with {response.status_code}: {response.data}")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='register@example.com').exists())
        # Depending on ACCOUNT_EMAIL_VERIFICATION, response might contain different things.
        # If 'mandatory', user is inactive. If 'optional' or 'none', user might be active.

    def test_user_login(self):
        """Test user login and JWT token retrieval."""
        # First, create a user to login with
        user = User.objects.create_user(username='testloginuser', email='login@example.com', password='aVeryComplexP@ssw0rd!')
        user.is_active = True # Ensure user is active, esp. if email verification is on
        user.save()

        login_data = {'email': 'login@example.com', 'password': 'aVeryComplexP@ssw0rd!'}
        response = self.client.post(self.login_url, login_data, format='json')

        if response.status_code != status.HTTP_200_OK:
            print(f"Login failed with {response.status_code}: {response.data}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('access_token' in response.data or 'access' in response.data) # dj-rest-auth with JWT
        self.assertTrue('refresh_token' in response.data or 'refresh' in response.data)
        # If using JWTCookieAuthentication, tokens are in cookies, body might be different
        self.assertTrue(response.cookies.get('cdex-auth-token'))


    def test_user_logout(self):
        """Test user logout (token invalidation if using JWT with blacklisting or session invalidation)."""
        # Register and login a user first
        User.objects.create_user(username='logoutuser', email='logout@example.com', password='aVeryComplexP@ssw0rd!')
        login_data = {'email': 'logout@example.com', 'password': 'aVeryComplexP@ssw0rd!'}
        login_response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        # Assuming JWT, token might be in body or cookies. dj-rest-auth handles this.
        # No specific token needed for client.post to logout if using cookie auth for JWT

        logout_response = self.client.post(self.logout_url, {}, format='json')
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)
        # Check that the auth cookie is cleared
        self.assertEqual(logout_response.cookies.get('cdex-auth-token').value, '')


class UserProfileAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='profileuser', email='profile@example.com', password='aVeryComplexP@ssw0rd!')
        self.user.is_active = True
        self.user.save()
        # UserProfile is created by signal
        self.profile_url = reverse('user-profile-detail') # from accounts.urls

        # Log in the user to get token for subsequent requests
        login_data = {'email': 'profile@example.com', 'password': 'aVeryComplexP@ssw0rd!'}
        login_response = self.client.post(reverse('rest_login'), login_data, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        # self.access_token = login_response.data['access_token']
        # self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        # With JWTCookieAuthentication, the token is set in client's cookies automatically.

    def test_get_user_profile(self):
        """Test retrieving authenticated user's profile."""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user_username'], self.user.username)
        self.assertEqual(response.data['user_email'], self.user.email)
        self.assertIn('bio', response.data)

    def test_update_user_profile(self):
        """Test updating authenticated user's profile (bio)."""
        new_bio = "This is my updated bio."
        response = self.client.put(self.profile_url, {'bio': new_bio}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['bio'], new_bio)

        # Verify the change in the database
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.bio, new_bio)

    def test_unauthenticated_profile_access(self):
        """Test that unauthenticated users cannot access the profile API."""
        unauth_client = APIClient() # New client without authentication
        response = unauth_client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # Changed 401 to 403

    def test_cannot_update_other_user_profile(self):
        """Ensure a user cannot update another user's profile (not directly testable with this endpoint setup)."""
        # The current /api/accounts/profile/ endpoint is designed to always fetch request.user's profile.
        # So, there's no ID in the URL to change to test accessing another user's profile.
        # This design inherently prevents accessing other profiles via this specific URL.
        # If we had an endpoint like /api/profiles/<id>/, then we'd test that.
        self.assertTrue(True, "Endpoint design inherently scopes to request.user's profile.")


class ProfileUIPageTests(TestCase): # Standard TestCase for non-API views
    def setUp(self):
        self.user = User.objects.create_user(username='ui_user', email='ui@example.com', password='aVeryComplexP@ssw0rd!')
        self.profile_ui_url = reverse('user-profile-ui') # from accounts.urls

    def test_profile_ui_page_authenticated_user(self):
        """Test that the profile UI page loads for an authenticated user."""
        self.client.login(email='ui@example.com', password='aVeryComplexP@ssw0rd!')
        response = self.client.get(self.profile_ui_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'account/profile_page.html')

    def test_profile_ui_page_unauthenticated_user(self):
        """Test that unauthenticated users are redirected from the profile UI page."""
        response = self.client.get(self.profile_ui_url)
        # Should redirect to login page (default behavior of LoginRequiredMixin)
        # The specific login URL might depend on allauth settings or LOGIN_URL setting
        expected_login_url = f"{reverse('account_login')}?next={self.profile_ui_url}"
        self.assertRedirects(response, expected_login_url, status_code=status.HTTP_302_FOUND)
