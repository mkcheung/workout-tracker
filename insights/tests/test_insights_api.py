
from exercises.models import (
    Exercise,
)
from datetime import datetime, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import path, reverse
from django.utils import timezone

from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.test import APITestCase
from workouts.models import (
    Workout,
    WorkoutExercise,
    WorkoutSet
)

from tests.factories import (
    create_user,
    create_workout,
    create_exercise
)

INSIGHTS_EXERCISE_SERIES_URL = reverse("insights:exercise-series")
def default_insights_exercise_url(workout_id):
    return reverse("workouts:workouts-detail", args=[workout_id])

User = get_user_model()
WORKOUT_URL = reverse("workouts:workouts-list")
def default_workout_url(workout_id):
    return reverse("workouts:workouts-detail", args=[workout_id])
WORKOUT_EXERCISE_URL = reverse("workouts:workout-exercises-list")
def default_workout_exercise_url(workout_exercise_id):
    return reverse("workouts:workout-exercises-detail", args=[workout_exercise_id])
WORKOUT_SET_URL = reverse("workouts:workout-sets-list")
def default_workout_set_url(workout_set_id):
    return reverse("workouts:workout-sets-detail", args=[workout_set_id])

class PrivateAuthApiTests(APITestCase):
    def setUp(self):
        self.user = create_user()
        self.client = APIClient()

    def test_create_workout_set(self):
        self.client.force_authenticate(self.user)
        current_datetime = timezone.now()
        one_day_before = current_datetime - timedelta(days=1)
        one_day_after = current_datetime + timedelta(days=1)
        workout_payload = {
            'user': self.user,
            'performed_at': current_datetime.isoformat()
        }
        workout = create_workout(**workout_payload)
        exercise = create_exercise()
        workout_exercise_payload = {
            'workout':workout.id,
            'exercise':exercise.id,
            'order': 1,
        }

        res = self.client.post(WORKOUT_EXERCISE_URL, workout_exercise_payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        data = res.data.get('results', res.data.get('data', res.data))
        self.assertEqual(workout.id, data['workout'])
        self.assertEqual(exercise.id, data['exercise'])
        self.assertEqual(workout_exercise_payload['order'], data['order'])

        workout_set_payload = {
            'workout_exercise': data['id'],
            'set_number':1,
            'reps':8,
            'weight':135
        }

        res = self.client.post(WORKOUT_SET_URL, workout_set_payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        data = res.data.get('results', res.data.get('data', res.data))
        self.assertEqual(workout_set_payload['workout_exercise'], data['workout_exercise'])
        self.assertEqual(workout_set_payload['set_number'], data['set_number'])
        self.assertEqual(workout_set_payload['reps'], data['reps'])
        self.assertEqual(workout_set_payload['weight'], Decimal(data['weight']))

        insights_payload = {
            'exercise_id': exercise.id,
            'metric': 'top_set_weight',
            'performed_from':one_day_before.strftime('%Y-%m-%d'),
            'performed_to':one_day_after.strftime('%Y-%m-%d')
        }
        res = self.client.get(INSIGHTS_EXERCISE_SERIES_URL, insights_payload)
        data = res.data.get('results', res.data.get('data', res.data))
        print(data)