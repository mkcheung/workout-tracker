from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.test import APITestCase
from exercises.models import (
    Exercise,
)
User = get_user_model()
# List/Create: reverse("exercises:exercise-list")
# Retrieve/Update/Delete: reverse("exercises:exercise-detail", args=[id])

EXERCISE_URL = reverse("exercises:exercise-list")
def exercise_detail_url(exercise_id):
    return reverse("exercises:exercise-detail", args=[exercise_id])

def create_admin_user(**params):
    defaults = {
        'username': 'testingadmin123',
        'email': 'admin@gmail,com',
        'password': 'testpassword123',
    }
    defaults.update(params)
    password = defaults.pop("password")
    superuser = User.objects.create_superuser(**defaults)
    superuser.set_password(password)
    return superuser

def create_user(**params):
    defaults = {
        'username': 'testing123',
        'email':'heyhey@gmail.com',
        'first_name':'first',
        'last_name':'last',
        'password':'testpassword123'
    }
    defaults.update(params)
    password = defaults.pop("password")
    user = User.objects.create_user(**defaults)
    user.set_password(password)
    return user


class PublicAuthApiTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
    
    def test_unauthenticated_access(self):
        res = self.client.get(EXERCISE_URL)
        self.assertIn(res.status_code, [status.HTTP_200_OK])


class PrivateAuthApiTests(APITestCase):
    def setUp(self):
        self.admin_user = create_admin_user()
        self.client = APIClient()
        self.user = create_user()

    def test_create_exercise_as_user(self):
        self.client.force_authenticate(user=self.user)
        payload = {
            'name':'Bench Press',
            'category':'push',
            'muscle_group':'chest',
            'is_active':True
        }
        res = self.client.post(EXERCISE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_exercise_as_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            'name':'Bench Press',
            'category':'push',
            'muscle_group':'chest',
            'is_active':True
        }
        res = self.client.post(EXERCISE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        data = res.data.get('results', res.data.get('data', res.data))
        self.assertEqual(data['name'], payload['name'])
        self.assertEqual(data['category'], payload['category'])
        self.assertEqual(data['muscle_group'], payload['muscle_group'])

    def test_update_exercise_as_user(self):
        self.client.force_authenticate(user=self.user)
        exercise = Exercise.objects.create(name='Bench Press', category='push',muscle_group='chest')
        payload = {
            'name':'Squat',
            'muscle_group':'legs'
        }
        res = self.client.patch(exercise_detail_url(exercise.id), payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_exercise_as_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        exercise = Exercise.objects.create(name='Bench Press', category='push',muscle_group='chest')
        payload = {
            'name':'Squat',
            'muscle_group':'legs'
        }
        res = self.client.patch(exercise_detail_url(exercise.id), payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.data.get('results', res.data.get('data', res.data))
        self.assertEqual(data['name'], payload['name'])
        self.assertEqual(data['muscle_group'], payload['muscle_group'])

    def test_delete_exercise_as_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        exercise = Exercise.objects.create(name='Bench Press', category='push',muscle_group='chest')

        res = self.client.delete(exercise_detail_url(exercise.id))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Exercise.objects.filter(id=exercise.id).exists())

    def test_delete_exercise_as_user(self):
        self.client.force_authenticate(user=self.user)
        exercise = Exercise.objects.create(name='Bench Press', category='push',muscle_group='chest')

        res = self.client.delete(exercise_detail_url(exercise.id))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Exercise.objects.filter(id=exercise.id).exists())
    