
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
INSIGHTS_WORKOUT_VOLUME_URL = reverse("insights:weekly-volume")
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

    def test_exercise_series_insights(self):
        self.client.force_authenticate(self.user)
        current_datetime = timezone.make_aware(datetime(2026, 2, 2, 12, 0, 0))
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
        workout1_exercise1_best_weight = 175

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
            'weight':workout1_exercise1_best_weight
        }

        res = self.client.post(WORKOUT_SET_URL, workout_set_payload)

        exercise2 = create_exercise(**{
            'name': 'another exercise',
            'category': 'pull',
            'muscle_group': 'legs'
        })
        workout1_exercise2_best_weight = 225

        workout_exercise_payload = {
            'workout':workout.id,
            'exercise':exercise2.id,
            'order': 2,
        }
        res = self.client.post(WORKOUT_EXERCISE_URL, workout_exercise_payload)
        data = res.data.get('results', res.data.get('data', res.data))

        workout_set_payload = {
            'workout_exercise': data['id'],
            'set_number':1,
            'reps':8,
            'weight':200
        }

        res = self.client.post(WORKOUT_SET_URL, workout_set_payload)

        workout_set_payload = {
            'workout_exercise': data['id'],
            'set_number':2,
            'reps':8,
            'weight':225
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
        workout2_exercise1_best_weight = 190

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
            'weight':workout2_exercise1_best_weight
        }
        
        res = self.client.post(WORKOUT_SET_URL, workout_set_payload)

        workout_exercise_payload = {
            'workout':workout_2.id,
            'exercise':exercise2.id,
            'order': 2,
        }
        res = self.client.post(WORKOUT_EXERCISE_URL, workout_exercise_payload)
        data = res.data.get('results', res.data.get('data', res.data))
        workout2_exercise2_best_weight = 250

        workout_set_payload = {
            'workout_exercise': data['id'],
            'set_number':1,
            'reps':8,
            'weight':245
        }

        res = self.client.post(WORKOUT_SET_URL, workout_set_payload)

        workout_set_payload = {
            'workout_exercise': data['id'],
            'set_number':2,
            'reps':8,
            'weight':250
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

        # test for exercise 1
        res = self.client.get(INSIGHTS_EXERCISE_SERIES_URL, insights_payload)
        data = res.data.get('results', res.data.get('data', res.data))
        workout_weeks = week_buckets(previous_time_marker,post_time_marker)
        points = data['points']
        summary = data['summary']
        self.assertEqual(data['exercise_id'], exercise.id)
        self.assertEqual(data['unit'], 'lbs_reps')
        self.assertEqual(data['metric'], 'top_set_weight')
        self.assertEqual(workout_weeks[0], points[0])
        self.assertEqual(workout_weeks[1], points[1])
        self.assertEqual(workout_weeks[2]['date'], points[2]['date'])
        self.assertEqual(Decimal(workout1_exercise1_best_weight), points[2]['value'])
        self.assertEqual(workout_weeks[3]['date'], points[3]['date'])
        self.assertEqual(Decimal(workout2_exercise1_best_weight), points[3]['value'])
        self.assertEqual(0, summary['start'])
        self.assertEqual(Decimal(workout2_exercise1_best_weight), summary['latest'])
        self.assertEqual(Decimal(workout2_exercise1_best_weight), summary['change'])

        # test for exercise 2
        insights_payload = {
            'exercise_id': exercise2.id,
            'metric': 'top_set_weight',
            'performed_from':previous_time_marker.strftime('%Y-%m-%d'),
            'performed_to':post_time_marker.strftime('%Y-%m-%d')
        }
        res = self.client.get(INSIGHTS_EXERCISE_SERIES_URL, insights_payload)
        data = res.data.get('results', res.data.get('data', res.data))
        workout_weeks = week_buckets(previous_time_marker,post_time_marker)
        points = data['points']
        summary = data['summary']
        self.assertEqual(data['exercise_id'], exercise2.id)
        self.assertEqual(data['unit'], 'lbs_reps')
        self.assertEqual(data['metric'], 'top_set_weight')
        self.assertEqual(workout_weeks[0], points[0])
        self.assertEqual(workout_weeks[1], points[1])
        self.assertEqual(workout_weeks[2]['date'], points[2]['date'])
        self.assertEqual(Decimal(workout1_exercise2_best_weight), points[2]['value'])
        self.assertEqual(workout_weeks[3]['date'], points[3]['date'])
        self.assertEqual(Decimal(workout2_exercise2_best_weight), points[3]['value'])
        self.assertEqual(0, summary['start'])
        self.assertEqual(Decimal(workout2_exercise2_best_weight), summary['latest'])
        self.assertEqual(Decimal(workout2_exercise2_best_weight), summary['change'])

    def test_exercise_series_insights_1_rep_max(self):
        self.client.force_authenticate(self.user)
        current_datetime = timezone.make_aware(datetime(2026, 2, 2, 12, 0, 0))
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
        workout1_exercise1_best_weight = 175

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
            'weight':workout1_exercise1_best_weight
        }
        workout1_exercise1_1_rep_max = round(workout1_exercise1_best_weight * (1 + (workout_set_payload['reps'] / Decimal(30))),2)

        res = self.client.post(WORKOUT_SET_URL, workout_set_payload)

        exercise2 = create_exercise(**{
            'name': 'another exercise',
            'category': 'pull',
            'muscle_group': 'legs'
        })
        workout1_exercise2_best_weight = 225

        workout_exercise_payload = {
            'workout':workout.id,
            'exercise':exercise2.id,
            'order': 2,
        }
        res = self.client.post(WORKOUT_EXERCISE_URL, workout_exercise_payload)
        data = res.data.get('results', res.data.get('data', res.data))

        workout_set_payload = {
            'workout_exercise': data['id'],
            'set_number':1,
            'reps':8,
            'weight':200
        }

        res = self.client.post(WORKOUT_SET_URL, workout_set_payload)

        workout_set_payload = {
            'workout_exercise': data['id'],
            'set_number':2,
            'reps':8,
            'weight':225
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
        workout2_exercise1_best_weight = 190

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
            'weight':workout2_exercise1_best_weight
        }
        workout2_exercise1_1_rep_max = round(workout2_exercise1_best_weight * (1 + (workout_set_payload['reps'] / Decimal(30))),2)
        
        res = self.client.post(WORKOUT_SET_URL, workout_set_payload)

        workout_exercise_payload = {
            'workout':workout_2.id,
            'exercise':exercise2.id,
            'order': 2,
        }
        res = self.client.post(WORKOUT_EXERCISE_URL, workout_exercise_payload)
        data = res.data.get('results', res.data.get('data', res.data))
        workout2_exercise2_best_weight = 250

        workout_set_payload = {
            'workout_exercise': data['id'],
            'set_number':1,
            'reps':8,
            'weight':245
        }

        res = self.client.post(WORKOUT_SET_URL, workout_set_payload)

        workout_set_payload = {
            'workout_exercise': data['id'],
            'set_number':2,
            'reps':8,
            'weight':250
        }

        res = self.client.post(WORKOUT_SET_URL, workout_set_payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        data = res.data.get('results', res.data.get('data', res.data))

        insights_payload = {
            'exercise_id': exercise.id,
            'metric': 'estimated_1rm',
            'performed_from':previous_time_marker.strftime('%Y-%m-%d'),
            'performed_to':post_time_marker.strftime('%Y-%m-%d')
        }

        # test for exercise 1
        res = self.client.get(INSIGHTS_EXERCISE_SERIES_URL, insights_payload)
        data = res.data.get('results', res.data.get('data', res.data))
        points = data['points']
        summary = data['summary']
        self.assertEqual(data['exercise_id'], exercise.id)
        self.assertEqual(data['unit'], 'lbs_reps')
        self.assertEqual(data['metric'], 'estimated_1rm')
        self.assertEqual(current_datetime.strftime('%Y-%m-%d'), points[0]['date'])
        self.assertEqual(Decimal(workout1_exercise1_1_rep_max), points[0]['value'])
        self.assertEqual(post_time_marker.strftime('%Y-%m-%d'), points[1]['date'])
        self.assertEqual(Decimal(workout2_exercise1_1_rep_max), points[1]['value'])
        self.assertEqual(Decimal(workout1_exercise1_1_rep_max), summary['start'])
        self.assertEqual(Decimal(workout2_exercise1_1_rep_max), summary['latest'])
        change = abs(workout2_exercise1_1_rep_max - workout1_exercise1_1_rep_max)
        self.assertEqual(change, summary['change'])

    def test_exercise_series_insights_tonnage(self):
        self.client.force_authenticate(self.user)
        current_datetime = timezone.make_aware(datetime(2026, 2, 2, 12, 0, 0))
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
        workout1_exercise1_tonnage = 0

        workout_set_payload = {
            'workout_exercise': data['id'],
            'set_number':1,
            'reps':8,
            'weight':135
        }

        res = self.client.post(WORKOUT_SET_URL, workout_set_payload)
        workout1_exercise1_tonnage += round(workout_set_payload['reps'] * workout_set_payload['weight'],2)

        workout_set_payload = {
            'workout_exercise': data['id'],
            'set_number':2,
            'reps':1,
            'weight':175
        }

        res = self.client.post(WORKOUT_SET_URL, workout_set_payload)
        workout1_exercise1_tonnage += round(workout_set_payload['reps'] * workout_set_payload['weight'],2)

        exercise2 = create_exercise(**{
            'name': 'another exercise',
            'category': 'pull',
            'muscle_group': 'legs'
        })
        workout1_exercise2_tonnage = 0

        workout_exercise_payload = {
            'workout':workout.id,
            'exercise':exercise2.id,
            'order': 2,
        }
        res = self.client.post(WORKOUT_EXERCISE_URL, workout_exercise_payload)
        data = res.data.get('results', res.data.get('data', res.data))

        workout_set_payload = {
            'workout_exercise': data['id'],
            'set_number':1,
            'reps':8,
            'weight':200
        }

        res = self.client.post(WORKOUT_SET_URL, workout_set_payload)
        workout1_exercise2_tonnage += round(workout_set_payload['reps'] * workout_set_payload['weight'],2)

        workout_set_payload = {
            'workout_exercise': data['id'],
            'set_number':2,
            'reps':8,
            'weight':225
        }

        res = self.client.post(WORKOUT_SET_URL, workout_set_payload)
        workout1_exercise2_tonnage += round(workout_set_payload['reps'] * workout_set_payload['weight'],2)

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
        workout2_exercise1_tonnage = 0

        workout_set_payload = {
            'workout_exercise': data['id'],
            'set_number':1,
            'reps':3,
            'weight':155
        }

        res = self.client.post(WORKOUT_SET_URL, workout_set_payload)
        workout2_exercise1_tonnage += round(workout_set_payload['reps'] * workout_set_payload['weight'],2)

        workout_set_payload = {
            'workout_exercise': data['id'],
            'set_number':2,
            'reps':1,
            'weight':190
        }
        
        res = self.client.post(WORKOUT_SET_URL, workout_set_payload)
        workout2_exercise1_tonnage += round(workout_set_payload['reps'] * workout_set_payload['weight'],2)

        workout_exercise_payload = {
            'workout':workout_2.id,
            'exercise':exercise2.id,
            'order': 2,
        }
        res = self.client.post(WORKOUT_EXERCISE_URL, workout_exercise_payload)
        data = res.data.get('results', res.data.get('data', res.data))
        workout2_exercise2_tonnage = 0

        workout_set_payload = {
            'workout_exercise': data['id'],
            'set_number':1,
            'reps':8,
            'weight':245
        }

        res = self.client.post(WORKOUT_SET_URL, workout_set_payload)
        workout2_exercise2_tonnage += round(workout_set_payload['reps'] * workout_set_payload['weight'],2)

        workout_set_payload = {
            'workout_exercise': data['id'],
            'set_number':2,
            'reps':8,
            'weight':250
        }

        res = self.client.post(WORKOUT_SET_URL, workout_set_payload)
        workout2_exercise2_tonnage += round(workout_set_payload['reps'] * workout_set_payload['weight'],2)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        data = res.data.get('results', res.data.get('data', res.data))

        insights_payload = {
            'exercise_id': exercise.id,
            'metric': 'tonnage',
            'performed_from':previous_time_marker.strftime('%Y-%m-%d'),
            'performed_to':post_time_marker.strftime('%Y-%m-%d')
        }

        # test for exercise 1

        res = self.client.get(INSIGHTS_EXERCISE_SERIES_URL, insights_payload)
        data = res.data.get('results', res.data.get('data', res.data))
        points = data['points']
        summary = data['summary']
        self.assertEqual(data['exercise_id'], exercise.id)
        self.assertEqual(data['unit'], 'lbs_reps')
        self.assertEqual(data['metric'], 'tonnage')
        self.assertEqual(current_datetime.strftime('%Y-%m-%d'), points[0]['date'])
        self.assertEqual(Decimal(workout1_exercise1_tonnage), points[0]['value'])
        self.assertEqual(post_time_marker.strftime('%Y-%m-%d'), points[1]['date'])
        self.assertEqual(Decimal(workout2_exercise1_tonnage), points[1]['value'])
        self.assertEqual(Decimal(workout1_exercise1_tonnage), summary['start'])
        self.assertEqual(Decimal(workout2_exercise1_tonnage), summary['latest'])
        change = abs(workout2_exercise1_tonnage - workout1_exercise1_tonnage)
        self.assertEqual(change, summary['change'])

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

    def test_exercise_series_insights(self):
        self.client.force_authenticate(self.user)
        current_datetime = timezone.make_aware(datetime(2026, 2, 2, 12, 0, 0))
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
        workout1_exercise1_best_weight = 175

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
            'weight':workout1_exercise1_best_weight
        }

        res = self.client.post(WORKOUT_SET_URL, workout_set_payload)

        exercise2 = create_exercise(**{
            'name': 'another exercise',
            'category': 'pull',
            'muscle_group': 'legs'
        })
        workout1_exercise2_best_weight = 225

        workout_exercise_payload = {
            'workout':workout.id,
            'exercise':exercise2.id,
            'order': 2,
        }
        res = self.client.post(WORKOUT_EXERCISE_URL, workout_exercise_payload)
        data = res.data.get('results', res.data.get('data', res.data))

        workout_set_payload = {
            'workout_exercise': data['id'],
            'set_number':1,
            'reps':8,
            'weight':200
        }

        res = self.client.post(WORKOUT_SET_URL, workout_set_payload)

        workout_set_payload = {
            'workout_exercise': data['id'],
            'set_number':2,
            'reps':8,
            'weight':225
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
        workout2_exercise1_best_weight = 190

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
            'weight':workout2_exercise1_best_weight
        }
        
        res = self.client.post(WORKOUT_SET_URL, workout_set_payload)

        workout_exercise_payload = {
            'workout':workout_2.id,
            'exercise':exercise2.id,
            'order': 2,
        }
        res = self.client.post(WORKOUT_EXERCISE_URL, workout_exercise_payload)
        data = res.data.get('results', res.data.get('data', res.data))
        workout2_exercise2_best_weight = 250

        workout_set_payload = {
            'workout_exercise': data['id'],
            'set_number':1,
            'reps':8,
            'weight':245
        }

        res = self.client.post(WORKOUT_SET_URL, workout_set_payload)

        workout_set_payload = {
            'workout_exercise': data['id'],
            'set_number':2,
            'reps':8,
            'weight':250
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

        # test for exercise 1
        res = self.client.get(INSIGHTS_EXERCISE_SERIES_URL, insights_payload)
        data = res.data.get('results', res.data.get('data', res.data))
        workout_weeks = week_buckets(previous_time_marker,post_time_marker)
        points = data['points']
        summary = data['summary']
        self.assertEqual(data['exercise_id'], exercise.id)
        self.assertEqual(data['unit'], 'lbs_reps')
        self.assertEqual(data['metric'], 'top_set_weight')
        self.assertEqual(workout_weeks[0], points[0])
        self.assertEqual(workout_weeks[1], points[1])
        self.assertEqual(workout_weeks[2]['date'], points[2]['date'])
        self.assertEqual(Decimal(workout1_exercise1_best_weight), points[2]['value'])
        self.assertEqual(workout_weeks[3]['date'], points[3]['date'])
        self.assertEqual(Decimal(workout2_exercise1_best_weight), points[3]['value'])
        self.assertEqual(0, summary['start'])
        self.assertEqual(Decimal(workout2_exercise1_best_weight), summary['latest'])
        self.assertEqual(Decimal(workout2_exercise1_best_weight), summary['change'])

        # test for exercise 2
        insights_payload = {
            'exercise_id': exercise2.id,
            'metric': 'top_set_weight',
            'performed_from':previous_time_marker.strftime('%Y-%m-%d'),
            'performed_to':post_time_marker.strftime('%Y-%m-%d')
        }
        res = self.client.get(INSIGHTS_EXERCISE_SERIES_URL, insights_payload)
        data = res.data.get('results', res.data.get('data', res.data))
        workout_weeks = week_buckets(previous_time_marker,post_time_marker)
        points = data['points']
        summary = data['summary']
        self.assertEqual(data['exercise_id'], exercise2.id)
        self.assertEqual(data['unit'], 'lbs_reps')
        self.assertEqual(data['metric'], 'top_set_weight')
        self.assertEqual(workout_weeks[0], points[0])
        self.assertEqual(workout_weeks[1], points[1])
        self.assertEqual(workout_weeks[2]['date'], points[2]['date'])
        self.assertEqual(Decimal(workout1_exercise2_best_weight), points[2]['value'])
        self.assertEqual(workout_weeks[3]['date'], points[3]['date'])
        self.assertEqual(Decimal(workout2_exercise2_best_weight), points[3]['value'])
        self.assertEqual(0, summary['start'])
        self.assertEqual(Decimal(workout2_exercise2_best_weight), summary['latest'])
        self.assertEqual(Decimal(workout2_exercise2_best_weight), summary['change'])

    def test_exercise_series_insights_1_rep_max(self):
        self.client.force_authenticate(self.user)
        current_datetime = timezone.make_aware(datetime(2026, 2, 2, 12, 0, 0))
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
        workout1_exercise1_best_weight = 175

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
            'weight':workout1_exercise1_best_weight
        }
        workout1_exercise1_1_rep_max = round(workout1_exercise1_best_weight * (1 + (workout_set_payload['reps'] / Decimal(30))),2)

        res = self.client.post(WORKOUT_SET_URL, workout_set_payload)

        exercise2 = create_exercise(**{
            'name': 'another exercise',
            'category': 'pull',
            'muscle_group': 'legs'
        })
        workout1_exercise2_best_weight = 225

        workout_exercise_payload = {
            'workout':workout.id,
            'exercise':exercise2.id,
            'order': 2,
        }
        res = self.client.post(WORKOUT_EXERCISE_URL, workout_exercise_payload)
        data = res.data.get('results', res.data.get('data', res.data))

        workout_set_payload = {
            'workout_exercise': data['id'],
            'set_number':1,
            'reps':8,
            'weight':200
        }

        res = self.client.post(WORKOUT_SET_URL, workout_set_payload)

        workout_set_payload = {
            'workout_exercise': data['id'],
            'set_number':2,
            'reps':8,
            'weight':225
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
        workout2_exercise1_best_weight = 190

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
            'weight':workout2_exercise1_best_weight
        }
        workout2_exercise1_1_rep_max = round(workout2_exercise1_best_weight * (1 + (workout_set_payload['reps'] / Decimal(30))),2)
        
        res = self.client.post(WORKOUT_SET_URL, workout_set_payload)

        workout_exercise_payload = {
            'workout':workout_2.id,
            'exercise':exercise2.id,
            'order': 2,
        }
        res = self.client.post(WORKOUT_EXERCISE_URL, workout_exercise_payload)
        data = res.data.get('results', res.data.get('data', res.data))
        workout2_exercise2_best_weight = 250

        workout_set_payload = {
            'workout_exercise': data['id'],
            'set_number':1,
            'reps':8,
            'weight':245
        }

        res = self.client.post(WORKOUT_SET_URL, workout_set_payload)

        workout_set_payload = {
            'workout_exercise': data['id'],
            'set_number':2,
            'reps':8,
            'weight':250
        }

        res = self.client.post(WORKOUT_SET_URL, workout_set_payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        data = res.data.get('results', res.data.get('data', res.data))

        insights_payload = {
            'exercise_id': exercise.id,
            'metric': 'estimated_1rm',
            'performed_from':previous_time_marker.strftime('%Y-%m-%d'),
            'performed_to':post_time_marker.strftime('%Y-%m-%d')
        }

        # test for exercise 1
        res = self.client.get(INSIGHTS_EXERCISE_SERIES_URL, insights_payload)
        data = res.data.get('results', res.data.get('data', res.data))
        points = data['points']
        summary = data['summary']
        self.assertEqual(data['exercise_id'], exercise.id)
        self.assertEqual(data['unit'], 'lbs_reps')
        self.assertEqual(data['metric'], 'estimated_1rm')
        self.assertEqual(current_datetime.strftime('%Y-%m-%d'), points[0]['date'])
        self.assertEqual(Decimal(workout1_exercise1_1_rep_max), points[0]['value'])
        self.assertEqual(post_time_marker.strftime('%Y-%m-%d'), points[1]['date'])
        self.assertEqual(Decimal(workout2_exercise1_1_rep_max), points[1]['value'])
        self.assertEqual(Decimal(workout1_exercise1_1_rep_max), summary['start'])
        self.assertEqual(Decimal(workout2_exercise1_1_rep_max), summary['latest'])
        change = abs(workout2_exercise1_1_rep_max - workout1_exercise1_1_rep_max)
        self.assertEqual(change, summary['change'])

    def test_exercise_series_insights_tonnage(self):
        self.client.force_authenticate(self.user)
        current_datetime = timezone.make_aware(datetime(2026, 2, 2, 12, 0, 0))
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
        workout1_exercise1_tonnage = 0

        workout_set_payload = {
            'workout_exercise': data['id'],
            'set_number':1,
            'reps':8,
            'weight':135
        }

        res = self.client.post(WORKOUT_SET_URL, workout_set_payload)
        workout1_exercise1_tonnage += round(workout_set_payload['reps'] * workout_set_payload['weight'],2)

        workout_set_payload = {
            'workout_exercise': data['id'],
            'set_number':2,
            'reps':1,
            'weight':175
        }

        res = self.client.post(WORKOUT_SET_URL, workout_set_payload)
        workout1_exercise1_tonnage += round(workout_set_payload['reps'] * workout_set_payload['weight'],2)

        exercise2 = create_exercise(**{
            'name': 'another exercise',
            'category': 'pull',
            'muscle_group': 'legs'
        })
        workout1_exercise2_tonnage = 0

        workout_exercise_payload = {
            'workout':workout.id,
            'exercise':exercise2.id,
            'order': 2,
        }
        res = self.client.post(WORKOUT_EXERCISE_URL, workout_exercise_payload)
        data = res.data.get('results', res.data.get('data', res.data))

        workout_set_payload = {
            'workout_exercise': data['id'],
            'set_number':1,
            'reps':8,
            'weight':200
        }

        res = self.client.post(WORKOUT_SET_URL, workout_set_payload)
        workout1_exercise2_tonnage += round(workout_set_payload['reps'] * workout_set_payload['weight'],2)

        workout_set_payload = {
            'workout_exercise': data['id'],
            'set_number':2,
            'reps':8,
            'weight':225
        }

        res = self.client.post(WORKOUT_SET_URL, workout_set_payload)
        workout1_exercise2_tonnage += round(workout_set_payload['reps'] * workout_set_payload['weight'],2)

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
        workout2_exercise1_tonnage = 0

        workout_set_payload = {
            'workout_exercise': data['id'],
            'set_number':1,
            'reps':3,
            'weight':155
        }

        res = self.client.post(WORKOUT_SET_URL, workout_set_payload)
        workout2_exercise1_tonnage += round(workout_set_payload['reps'] * workout_set_payload['weight'],2)

        workout_set_payload = {
            'workout_exercise': data['id'],
            'set_number':2,
            'reps':1,
            'weight':190
        }
        
        res = self.client.post(WORKOUT_SET_URL, workout_set_payload)
        workout2_exercise1_tonnage += round(workout_set_payload['reps'] * workout_set_payload['weight'],2)

        workout_exercise_payload = {
            'workout':workout_2.id,
            'exercise':exercise2.id,
            'order': 2,
        }
        res = self.client.post(WORKOUT_EXERCISE_URL, workout_exercise_payload)
        data = res.data.get('results', res.data.get('data', res.data))
        workout2_exercise2_tonnage = 0

        workout_set_payload = {
            'workout_exercise': data['id'],
            'set_number':1,
            'reps':8,
            'weight':245
        }

        res = self.client.post(WORKOUT_SET_URL, workout_set_payload)
        workout2_exercise2_tonnage += round(workout_set_payload['reps'] * workout_set_payload['weight'],2)

        workout_set_payload = {
            'workout_exercise': data['id'],
            'set_number':2,
            'reps':8,
            'weight':250
        }

        res = self.client.post(WORKOUT_SET_URL, workout_set_payload)
        workout2_exercise2_tonnage += round(workout_set_payload['reps'] * workout_set_payload['weight'],2)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        data = res.data.get('results', res.data.get('data', res.data))

        insights_payload = {
            'exercise_id': exercise.id,
            'metric': 'tonnage',
            'performed_from':previous_time_marker.strftime('%Y-%m-%d'),
            'performed_to':post_time_marker.strftime('%Y-%m-%d')
        }

        # test for exercise 1

        res = self.client.get(INSIGHTS_EXERCISE_SERIES_URL, insights_payload)
        data = res.data.get('results', res.data.get('data', res.data))
        points = data['points']
        summary = data['summary']
        self.assertEqual(data['exercise_id'], exercise.id)
        self.assertEqual(data['unit'], 'lbs_reps')
        self.assertEqual(data['metric'], 'tonnage')
        self.assertEqual(current_datetime.strftime('%Y-%m-%d'), points[0]['date'])
        self.assertEqual(Decimal(workout1_exercise1_tonnage), points[0]['value'])
        self.assertEqual(post_time_marker.strftime('%Y-%m-%d'), points[1]['date'])
        self.assertEqual(Decimal(workout2_exercise1_tonnage), points[1]['value'])
        self.assertEqual(Decimal(workout1_exercise1_tonnage), summary['start'])
        self.assertEqual(Decimal(workout2_exercise1_tonnage), summary['latest'])
        change = abs(workout2_exercise1_tonnage - workout1_exercise1_tonnage)
        self.assertEqual(change, summary['change'])

    def test_weekly_volume_for_exercise(self):
        duration = 12 # weeks
        self.client.force_authenticate(self.user)
        current_datetime = timezone.make_aware(datetime(2026, 1, 27, 12, 0, 0))
        previous_time_marker = current_datetime - timedelta(days=31)
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
            'weight':175
        }

        res = self.client.post(WORKOUT_SET_URL, workout_set_payload)

        workout_payload = {
            'user': self.user,
            'performed_at': previous_time_marker.isoformat()
        }
        workout_2 = create_workout(**workout_payload)
        workout_exercise_payload = {
            'workout':workout_2.id,
            'exercise':exercise.id,
            'order': 1,
        }

        res = self.client.post(WORKOUT_EXERCISE_URL, workout_exercise_payload)
        data = res.data.get('results', res.data.get('data', res.data))

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
            'weight':190
        }
        
        res = self.client.post(WORKOUT_SET_URL, workout_set_payload)

        workout_volume_payload = {
            'exercise_id': exercise.id,
            'weeks': duration,
            'to':current_datetime.strftime('%Y-%m-%d')
        }

        # test for exercise 1

        res = self.client.get(INSIGHTS_WORKOUT_VOLUME_URL, workout_volume_payload)
        data = res.data.get('results', res.data.get('data', res.data))
        points = data['points']
        pre_time_marker_str = (previous_time_marker - timedelta(previous_time_marker.weekday())).strftime('%Y-%m-%d')
        cur_time_marker_str = (current_datetime - timedelta(current_datetime.weekday())).strftime('%Y-%m-%d')
        self.assertEqual(data['exercise_id'], exercise.id)
        self.assertEqual(data['unit'], 'lbs_reps')
        self.assertEqual(data['weeks'], 12)
        self.assertEqual(pre_time_marker_str, points[pre_time_marker_str]['week_start'])
        self.assertEqual(1255.00, points[cur_time_marker_str]['value'])
        self.assertEqual(cur_time_marker_str, points[cur_time_marker_str]['week_start'])
        self.assertEqual(655.00, points[pre_time_marker_str]['value'])
