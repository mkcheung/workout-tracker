from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()
REGISTER_URL = reverse('accounts:register')
LOGIN_URL = reverse('accounts:login')
LOGOUT_URL = reverse('accounts:logout')
ME_URL = reverse('accounts:me')

User = get_user_model()

def create_user(**params):
    defaults = {
        "name": "Test Name",
        "email": "test@example.com",
        "username": "test@example.com",
        "password": "testpass123",
    }
    defaults.update(params)

    password = defaults.pop("password")
    user = User.objects.create_user(**defaults)
    user.set_password(password)
    user.save()
    return user

class PublicAuthApiTests(APITestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_creates_user(self):
        payload = {
            "name": "Test",
            "email": "testing123@example.com",
            "password": "testing123",
        }
        res = self.client.post(REGISTER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', res.data)
        self.assertIn('user', res.data)

        user = User.objects.get(email=payload['email'])
        self.assertEqual(res.data['user']['name'], user.name)
        self.assertEqual(res.data['user']['email'], user.email)
        self.assertEqual(user.name, payload['name'])
        self.assertTrue(user.check_password(payload["password"]))

    def test_register_creates_user_missing_name(self):
        payload = {
            "name": "",
            "email": "testing123@example.com",
            "password": "testing123",
            "password_confirm": "testing123",
        }
        res = self.client.post(REGISTER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_creates_user_missing_email(self):
        payload = {
            "name": "Test",
            "email": "",
            "password": "testing123",
        }
        res = self.client.post(REGISTER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_creates_user_missing_password(self):
        payload = {
            "name": "Test",
            "email": "testing123@example.com",
            "password": "",
        }
        res = self.client.post(REGISTER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_for_user(self):
        register_payload = {
            'email': 'test@example.com',
            'username': 'test@example.com',
            'password': 'testpass123',
            'name': 'Test Name',
        }
        res = self.client.post(REGISTER_URL, register_payload, format="json")
        payload = {
            'email': register_payload['email'],
            'password': register_payload['password']
        }
        res = self.client.post(LOGIN_URL, payload)
        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_incorrect_password(self):
        register_payload = {
            'email': 'test@example.com',
            'username': 'test@example.com',
            'password': 'testpass123',
            'name': 'Test Name',
        }
        res = self.client.post(REGISTER_URL, register_payload, format="json")
        payload = {
            'email': register_payload['email'],
            'password': 'testpas'
        }
        res = self.client.post(LOGIN_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_email(self):
        register_payload = {
            'email': 'test@example.com',
            'username': 'test@example.com',
            'password': 'testpass123',
            'name': 'Test Name',
        }
        res = self.client.post(REGISTER_URL, register_payload, format="json")
        payload = {
            'email': '',
            'password': 'testpass123'
        }
        res = self.client.post(LOGIN_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class PrivateAuthApiTests(APITestCase):
    def setUp(self):
        self.password = 'testpass123'
        self.user = create_user(password=self.password)
        self.client = APIClient()
    
    def test_logout(self):
        payload = {
            'email': self.user.email,
            'password': self.password
        }
        login_res = self.client.post(LOGIN_URL, payload)

        self.assertEqual(login_res.status_code, status.HTTP_200_OK)
        self.assertIn('token', login_res.data)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {login_res.data['token']}")
        res = self.client.post(LOGOUT_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_me(self):
        self.password = 'testpass123'
        payload = {
            'email': self.user.email,
            'password': self.password
        }
        login_res = self.client.post(LOGIN_URL, payload)
        self.assertEqual(login_res.status_code, status.HTTP_200_OK)
        self.assertIn('token', login_res.data)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {login_res.data['token']}")
        me_res = self.client.post(ME_URL)
        self.assertEqual(me_res.status_code, status.HTTP_200_OK)
 