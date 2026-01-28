
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

from insights.services import(
    week_buckets
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

    def test_scaffolding(self):
        self.client.force_authenticate(self.user)
        current_datetime = timezone.now()
        previous_time_marker = current_datetime - timedelta(days=10)
        post_time_marker = current_datetime + timedelta(days=10)
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
        data = res.data.get('results', res.data.get('data', res.data))
        workout1_best_weight = 175

        workout_set_payload = {
            'workout_exercise': data['id'],
            'set_number':1,
            'reps':8,
            'weight':135
        }

        res = self.client.post(WORKOUT_SET_URL, workout_set_payload)

        workout_set_payload = {
            'workout_exercise': data['id'],
            'set_number':2,
            'reps':1,
            'weight':workout1_best_weight
        }

        res = self.client.post(WORKOUT_SET_URL, workout_set_payload)

        workout_payload = {
            'user': self.user,
            'performed_at': post_time_marker.isoformat()
        }
        workout_2 = create_workout(**workout_payload)
        workout_exercise_payload = {
            'workout':workout_2.id,
            'exercise':exercise.id,
            'order': 1,
        }

        res = self.client.post(WORKOUT_EXERCISE_URL, workout_exercise_payload)
        data = res.data.get('results', res.data.get('data', res.data))
        workout2_best_weight = 190

        workout_set_payload = {
            'workout_exercise': data['id'],
            'set_number':1,
            'reps':3,
            'weight':155
        }

        res = self.client.post(WORKOUT_SET_URL, workout_set_payload)

        workout_set_payload = {
            'workout_exercise': data['id'],
            'set_number':2,
            'reps':1,
            'weight':workout2_best_weight
        }

        res = self.client.post(WORKOUT_SET_URL, workout_set_payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        data = res.data.get('results', res.data.get('data', res.data))

        insights_payload = {
            'exercise_id': exercise.id,
            'metric': 'top_set_weight',
            'performed_from':previous_time_marker.strftime('%Y-%m-%d'),
            'performed_to':post_time_marker.strftime('%Y-%m-%d')
        }
        res = self.client.get(INSIGHTS_EXERCISE_SERIES_URL, insights_payload)
        data = res.data.get('results', res.data.get('data', res.data))
        workout_weeks = week_buckets(previous_time_marker,post_time_marker)
        points = data['points']
        self.assertEqual(data['exercise_id'], exercise.id)
        self.assertEqual(data['unit'], 'lbs_reps')
        self.assertEqual(data['weeks'], 4)
        self.assertEqual(workout_weeks[0], points[0])
        self.assertEqual(workout_weeks[1], points[1])
        self.assertEqual(workout_weeks[2]['date'], points[2]['date'])
        self.assertEqual(Decimal(workout1_best_weight), points[2]['value'])
        self.assertEqual(workout_weeks[3]['date'], points[3]['date'])
        self.assertEqual(Decimal(workout2_best_weight), points[3]['value'])