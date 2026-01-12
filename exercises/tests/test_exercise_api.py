from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.test import APITestCase
from exercises.models import (
    Exercise,
)
# List/Create: reverse("exercises:exercise-list")
# Retrieve/Update/Delete: reverse("exercises:exercise-detail", args=[id])

EXERCISES_URL = reverse("exercises:exercise-list")
def exercise_detail_url(exercise_id):
    reverse("exercises:exercise-detail", args=[exercise_id])

class PublicAuthApiTests:
    def setUp(self):
        self.client = APIClient()
    
    def test_unauthenticated_access(self):
        res = self.client.get(EXERCISES_URL)
        self.assertIn(res.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])