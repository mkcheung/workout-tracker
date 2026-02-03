
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
INSIGHTS_EXPORT_SETS_URL = reverse("insights:export-sets")

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

    def test_export_sets_insights(self):
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

    def test_export_sets_insights(self):
        duration = 12 # weeks
        self.client.force_authenticate(self.user)
        current_datetime = timezone.make_aware(datetime(2026, 1, 27, 12, 0, 0))
        previous_time_marker = current_datetime - timedelta(days=31)
        post_time_marker = current_datetime + timedelta(days=10)
        workout_payload1 = {
            'user': self.user,
            'performed_at': current_datetime.isoformat()
        }
        workout1 = create_workout(**workout_payload1)
        exercise1 = create_exercise()
        exercise2 = create_exercise(**{
            'name':'exercise2'
        })
        workout1_exercise_payload1 = {
            'workout':workout1.id,
            'exercise':exercise1.id,
            'order': 1,
        }

        res = self.client.post(WORKOUT_EXERCISE_URL, workout1_exercise_payload1)
        data_workout1_exercise_payload1 = res.data.get('results', res.data.get('data', res.data))
        workout1_set_payload1 = {
            'workout_exercise': data_workout1_exercise_payload1['id'],
            'set_number':1,
            'reps':8,
            'weight':135
        }

        res = self.client.post(WORKOUT_SET_URL, workout1_set_payload1)
        data_workout1_set_payload1 = res.data.get('results', res.data.get('data', res.data))

        workout1_set_payload2 = {
            'workout_exercise': data_workout1_exercise_payload1['id'],
            'set_number':2,
            'reps':1,
            'weight':175
        }

        res = self.client.post(WORKOUT_SET_URL, workout1_set_payload2)
        data_workout1_set_payload2 = res.data.get('results', res.data.get('data', res.data))


        workout1_exercise_payload2 = {
            'workout':workout1.id,
            'exercise':exercise2.id,
            'order': 2,
        }

        res = self.client.post(WORKOUT_EXERCISE_URL, workout1_exercise_payload2)
        data_workout1_exercise_payload2 = res.data.get('results', res.data.get('data', res.data))
        workout1_ex2_set_payload1 = {
            'workout_exercise': data_workout1_exercise_payload2['id'],
            'set_number':1,
            'reps':8,
            'weight':135
        }

        res = self.client.post(WORKOUT_SET_URL, workout1_ex2_set_payload1)
        data_workout1_ex2_set_payload1 = res.data.get('results', res.data.get('data', res.data))

        workout1_ex2_set_payload2 = {
            'workout_exercise': data_workout1_exercise_payload2['id'],
            'set_number':2,
            'reps':1,
            'weight':175
        }

        res = self.client.post(WORKOUT_SET_URL, workout1_ex2_set_payload2)
        data_workout1_ex2_set_payload2 = res.data.get('results', res.data.get('data', res.data))


        workout_payload2 = {
            'user': self.user,
            'performed_at': previous_time_marker.isoformat()
        }
        workout_2 = create_workout(**workout_payload2)
        workout2_exercise_payload1 = {
            'workout':workout_2.id,
            'exercise':exercise1.id,
            'order': 1,
        }

        res = self.client.post(WORKOUT_EXERCISE_URL, workout2_exercise_payload1)
        data_workout2_exercise_payload1 = res.data.get('results', res.data.get('data', res.data))

        workout2_set_payload1 = {
            'workout_exercise': data_workout2_exercise_payload1['id'],
            'set_number':1,
            'reps':3,
            'weight':155
        }

        res = self.client.post(WORKOUT_SET_URL, workout2_set_payload1)
        data_workout2_set_payload1 = res.data.get('results', res.data.get('data', res.data))

        workout2_set_payload2 = {
            'workout_exercise': data_workout2_exercise_payload1['id'],
            'set_number':2,
            'reps':1,
            'weight':190
        }
        
        res = self.client.post(WORKOUT_SET_URL, workout2_set_payload2)
        data_workout2_set_payload2 = res.data.get('results', res.data.get('data', res.data))

        insights_payload = {
            'performed_from':previous_time_marker.strftime('%Y-%m-%d'),
            'performed_to':current_datetime.strftime('%Y-%m-%d')
        }

        res = self.client.get(INSIGHTS_EXPORT_SETS_URL, insights_payload)
        data = res.data.get('results', res.data.get('data', res.data))
        dt_object = datetime.fromisoformat(workout1.performed_at)
        performed_date_string = dt_object.date()

        self.assertEqual('/api/insightsexport_sets/?page=1&page_size=200',res.data.get('next'))
        self.assertFalse(res.data.get('previous'))
        self.assertEqual(6, len(data))
        self.assertEqual(data[0]['workout_id'], workout1.id)
        self.assertEqual(data[0]['performed_at'], performed_date_string.strftime('%Y-%m-%d'))
        self.assertEqual(data[0]['exercise_id'], exercise1.id)
        self.assertEqual(data[0]['exercise_name'], exercise1.name)
        self.assertEqual(data[0]['workout_exercise_id'], data_workout1_exercise_payload1['id'])
        self.assertEqual(data[0]['order'], data_workout1_exercise_payload1['order'])
        self.assertEqual(data[0]['set_id'], data_workout1_set_payload1['id'])
        self.assertEqual(data[0]['set_number'], data_workout1_set_payload1['set_number'])
        self.assertEqual(data[0]['reps'], data_workout1_set_payload1['reps'])
        self.assertEqual(data[0]['weight'], Decimal(data_workout1_set_payload1['weight']))

        self.assertEqual(data[1]['workout_id'], workout1.id)
        self.assertEqual(data[1]['performed_at'], performed_date_string.strftime('%Y-%m-%d'))
        self.assertEqual(data[1]['exercise_id'], exercise1.id)
        self.assertEqual(data[1]['exercise_name'], exercise1.name)
        self.assertEqual(data[1]['workout_exercise_id'], data_workout1_exercise_payload1['id'])
        self.assertEqual(data[1]['order'], data_workout1_exercise_payload1['order'])
        self.assertEqual(data[1]['set_id'], data_workout1_set_payload2['id'])
        self.assertEqual(data[1]['set_number'], data_workout1_set_payload2['set_number'])
        self.assertEqual(data[1]['reps'], data_workout1_set_payload2['reps'])
        self.assertEqual(data[1]['weight'], Decimal(data_workout1_set_payload2['weight']))

        self.assertEqual(data[2]['workout_id'], workout1.id)
        self.assertEqual(data[2]['performed_at'], performed_date_string.strftime('%Y-%m-%d'))
        self.assertEqual(data[2]['exercise_id'], exercise2.id)
        self.assertEqual(data[2]['exercise_name'], exercise2.name)
        self.assertEqual(data[2]['workout_exercise_id'], data_workout1_exercise_payload2['id'])
        self.assertEqual(data[2]['order'], data_workout1_exercise_payload2['order'])
        self.assertEqual(data[2]['set_id'], data_workout1_ex2_set_payload1['id'])
        self.assertEqual(data[2]['set_number'], data_workout1_ex2_set_payload1['set_number'])
        self.assertEqual(data[2]['reps'], data_workout1_ex2_set_payload1['reps'])
        self.assertEqual(data[2]['weight'], Decimal(data_workout1_ex2_set_payload1['weight']))

        self.assertEqual(data[3]['workout_id'], workout1.id)
        self.assertEqual(data[3]['performed_at'], performed_date_string.strftime('%Y-%m-%d'))
        self.assertEqual(data[3]['exercise_id'], exercise2.id)
        self.assertEqual(data[3]['exercise_name'], exercise2.name)
        self.assertEqual(data[3]['workout_exercise_id'], data_workout1_exercise_payload2['id'])
        self.assertEqual(data[3]['order'], data_workout1_exercise_payload2['order'])
        self.assertEqual(data[3]['set_id'], data_workout1_ex2_set_payload2['id'])
        self.assertEqual(data[3]['set_number'], data_workout1_ex2_set_payload2['set_number'])
        self.assertEqual(data[3]['reps'], data_workout1_ex2_set_payload2['reps'])
        self.assertEqual(data[3]['weight'], Decimal(data_workout1_ex2_set_payload2['weight']))

        self.assertEqual(data[4]['workout_id'], workout_2.id)
        self.assertEqual(data[4]['performed_at'], previous_time_marker.date().strftime('%Y-%m-%d'))
        self.assertEqual(data[4]['exercise_id'], exercise1.id)
        self.assertEqual(data[4]['exercise_name'], exercise1.name)
        self.assertEqual(data[4]['workout_exercise_id'], data_workout2_exercise_payload1['id'])
        self.assertEqual(data[4]['order'], data_workout2_exercise_payload1['order'])
        self.assertEqual(data[4]['set_id'], data_workout2_set_payload1['id'])
        self.assertEqual(data[4]['set_number'], data_workout2_set_payload1['set_number'])
        self.assertEqual(data[4]['reps'], data_workout2_set_payload1['reps'])
        self.assertEqual(data[4]['weight'], Decimal(data_workout2_set_payload1['weight']))

        self.assertEqual(data[5]['workout_id'], workout_2.id)
        self.assertEqual(data[5]['performed_at'], previous_time_marker.date().strftime('%Y-%m-%d'))
        self.assertEqual(data[5]['exercise_id'], exercise1.id)
        self.assertEqual(data[5]['exercise_name'], exercise1.name)
        self.assertEqual(data[5]['workout_exercise_id'], data_workout2_exercise_payload1['id'])
        self.assertEqual(data[5]['order'], data_workout2_exercise_payload1['order'])
        self.assertEqual(data[5]['set_id'], data_workout2_set_payload2['id'])
        self.assertEqual(data[5]['set_number'], data_workout2_set_payload2['set_number'])
        self.assertEqual(data[5]['reps'], data_workout2_set_payload2['reps'])
        self.assertEqual(data[5]['weight'], Decimal(data_workout2_set_payload2['weight']))

    def test_export_sets_insights_exercise_1(self):
        duration = 12 # weeks
        self.client.force_authenticate(self.user)
        current_datetime = timezone.make_aware(datetime(2026, 1, 27, 12, 0, 0))
        previous_time_marker = current_datetime - timedelta(days=31)
        post_time_marker = current_datetime + timedelta(days=10)
        workout_payload1 = {
            'user': self.user,
            'performed_at': current_datetime.isoformat()
        }
        workout1 = create_workout(**workout_payload1)
        exercise1 = create_exercise()
        workout1_exercise_payload1 = {
            'workout':workout1.id,
            'exercise':exercise1.id,
            'order': 1,
        }

        res = self.client.post(WORKOUT_EXERCISE_URL, workout1_exercise_payload1)
        data_workout1_exercise_payload1 = res.data.get('results', res.data.get('data', res.data))
        workout1_set_payload1 = {
            'workout_exercise': data_workout1_exercise_payload1['id'],
            'set_number':1,
            'reps':8,
            'weight':135
        }

        res = self.client.post(WORKOUT_SET_URL, workout1_set_payload1)
        data_workout1_set_payload1 = res.data.get('results', res.data.get('data', res.data))

        workout1_set_payload2 = {
            'workout_exercise': data_workout1_exercise_payload1['id'],
            'set_number':2,
            'reps':1,
            'weight':175
        }

        res = self.client.post(WORKOUT_SET_URL, workout1_set_payload2)
        data_workout1_set_payload2 = res.data.get('results', res.data.get('data', res.data))

        workout_payload2 = {
            'user': self.user,
            'performed_at': previous_time_marker.isoformat()
        }
        workout_2 = create_workout(**workout_payload2)
        workout2_exercise_payload1 = {
            'workout':workout_2.id,
            'exercise':exercise1.id,
            'order': 1,
        }

        res = self.client.post(WORKOUT_EXERCISE_URL, workout2_exercise_payload1)
        data_workout2_exercise_payload1 = res.data.get('results', res.data.get('data', res.data))

        workout2_set_payload1 = {
            'workout_exercise': data_workout2_exercise_payload1['id'],
            'set_number':1,
            'reps':3,
            'weight':155
        }

        res = self.client.post(WORKOUT_SET_URL, workout2_set_payload1)
        data_workout2_set_payload1 = res.data.get('results', res.data.get('data', res.data))

        workout2_set_payload2 = {
            'workout_exercise': data_workout2_exercise_payload1['id'],
            'set_number':2,
            'reps':1,
            'weight':190
        }
        
        res = self.client.post(WORKOUT_SET_URL, workout2_set_payload2)
        data_workout2_set_payload2 = res.data.get('results', res.data.get('data', res.data))

        insights_payload = {
            'exercise_id': exercise1.id,
            'performed_from':previous_time_marker.strftime('%Y-%m-%d'),
            'performed_to':current_datetime.strftime('%Y-%m-%d')
        }

        res = self.client.get(INSIGHTS_EXPORT_SETS_URL, insights_payload)
        data = res.data.get('results', res.data.get('data', res.data))

        dt_object = datetime.fromisoformat(workout1.performed_at)
        performed_date_string = dt_object.date()

        self.assertEqual('/api/insightsexport_sets/?page=1&page_size=200',res.data.get('next'))
        self.assertFalse(res.data.get('previous'))
        self.assertEqual(4, len(data))
        self.assertEqual(data[0]['workout_id'], workout1.id)
        self.assertEqual(data[0]['performed_at'], performed_date_string.strftime('%Y-%m-%d'))
        self.assertEqual(data[0]['exercise_id'], exercise1.id)
        self.assertEqual(data[0]['exercise_name'], exercise1.name)
        self.assertEqual(data[0]['workout_exercise_id'], data_workout1_exercise_payload1['id'])
        self.assertEqual(data[0]['order'], data_workout1_exercise_payload1['order'])
        self.assertEqual(data[0]['set_id'], data_workout1_set_payload1['id'])
        self.assertEqual(data[0]['set_number'], data_workout1_set_payload1['set_number'])
        self.assertEqual(data[0]['reps'], data_workout1_set_payload1['reps'])
        self.assertEqual(data[0]['weight'], Decimal(data_workout1_set_payload1['weight']))

        self.assertEqual(data[1]['workout_id'], workout1.id)
        self.assertEqual(data[1]['performed_at'], performed_date_string.strftime('%Y-%m-%d'))
        self.assertEqual(data[1]['exercise_id'], exercise1.id)
        self.assertEqual(data[1]['exercise_name'], exercise1.name)
        self.assertEqual(data[1]['workout_exercise_id'], data_workout1_exercise_payload1['id'])
        self.assertEqual(data[1]['order'], data_workout1_exercise_payload1['order'])
        self.assertEqual(data[1]['set_id'], data_workout1_set_payload2['id'])
        self.assertEqual(data[1]['set_number'], data_workout1_set_payload2['set_number'])
        self.assertEqual(data[1]['reps'], data_workout1_set_payload2['reps'])
        self.assertEqual(data[1]['weight'], Decimal(data_workout1_set_payload2['weight']))

        self.assertEqual(data[2]['workout_id'], workout_2.id)
        self.assertEqual(data[2]['performed_at'], previous_time_marker.date().strftime('%Y-%m-%d'))
        self.assertEqual(data[2]['exercise_id'], exercise1.id)
        self.assertEqual(data[2]['exercise_name'], exercise1.name)
        self.assertEqual(data[2]['workout_exercise_id'], data_workout2_exercise_payload1['id'])
        self.assertEqual(data[2]['order'], data_workout2_exercise_payload1['order'])
        self.assertEqual(data[2]['set_id'], data_workout2_set_payload1['id'])
        self.assertEqual(data[2]['set_number'], data_workout2_set_payload1['set_number'])
        self.assertEqual(data[2]['reps'], data_workout2_set_payload1['reps'])
        self.assertEqual(data[2]['weight'], Decimal(data_workout2_set_payload1['weight']))

        self.assertEqual(data[3]['workout_id'], workout_2.id)
        self.assertEqual(data[3]['performed_at'], previous_time_marker.date().strftime('%Y-%m-%d'))
        self.assertEqual(data[3]['exercise_id'], exercise1.id)
        self.assertEqual(data[3]['exercise_name'], exercise1.name)
        self.assertEqual(data[3]['workout_exercise_id'], data_workout2_exercise_payload1['id'])
        self.assertEqual(data[3]['order'], data_workout2_exercise_payload1['order'])
        self.assertEqual(data[3]['set_id'], data_workout2_set_payload2['id'])
        self.assertEqual(data[3]['set_number'], data_workout2_set_payload2['set_number'])
        self.assertEqual(data[3]['reps'], data_workout2_set_payload2['reps'])
        self.assertEqual(data[3]['weight'], Decimal(data_workout2_set_payload2['weight']))

    def test_export_sets_insights_exercise_2(self):
        duration = 12 # weeks
        self.client.force_authenticate(self.user)
        current_datetime = timezone.make_aware(datetime(2026, 1, 27, 12, 0, 0))
        previous_time_marker = current_datetime - timedelta(days=31)
        post_time_marker = current_datetime + timedelta(days=10)
        workout_payload1 = {
            'user': self.user,
            'performed_at': current_datetime.isoformat()
        }
        workout1 = create_workout(**workout_payload1)
        exercise1 = create_exercise()
        exercise2 = create_exercise(**{
            'name':'exercise2'
        })
        workout1_exercise_payload1 = {
            'workout':workout1.id,
            'exercise':exercise1.id,
            'order': 1,
        }

        res = self.client.post(WORKOUT_EXERCISE_URL, workout1_exercise_payload1)
        data_workout1_exercise_payload1 = res.data.get('results', res.data.get('data', res.data))
        workout1_set_payload1 = {
            'workout_exercise': data_workout1_exercise_payload1['id'],
            'set_number':1,
            'reps':8,
            'weight':135
        }

        res = self.client.post(WORKOUT_SET_URL, workout1_set_payload1)
        data_workout1_set_payload1 = res.data.get('results', res.data.get('data', res.data))

        workout1_set_payload2 = {
            'workout_exercise': data_workout1_exercise_payload1['id'],
            'set_number':2,
            'reps':1,
            'weight':175
        }

        res = self.client.post(WORKOUT_SET_URL, workout1_set_payload2)
        data_workout1_set_payload2 = res.data.get('results', res.data.get('data', res.data))

        workout_payload2 = {
            'user': self.user,
            'performed_at': previous_time_marker.isoformat()
        }
        workout_2 = create_workout(**workout_payload2)
        workout2_exercise_payload1 = {
            'workout':workout_2.id,
            'exercise':exercise2.id,
            'order': 1,
        }

        res = self.client.post(WORKOUT_EXERCISE_URL, workout2_exercise_payload1)
        data_workout2_exercise_payload1 = res.data.get('results', res.data.get('data', res.data))

        workout2_set_payload1 = {
            'workout_exercise': data_workout2_exercise_payload1['id'],
            'set_number':1,
            'reps':3,
            'weight':155
        }

        res = self.client.post(WORKOUT_SET_URL, workout2_set_payload1)
        data_workout2_set_payload1 = res.data.get('results', res.data.get('data', res.data))

        workout2_set_payload2 = {
            'workout_exercise': data_workout2_exercise_payload1['id'],
            'set_number':2,
            'reps':1,
            'weight':190
        }
        
        res = self.client.post(WORKOUT_SET_URL, workout2_set_payload2)
        data_workout2_set_payload2 = res.data.get('results', res.data.get('data', res.data))

        insights_payload = {
            'exercise_id': exercise2.id,
            'performed_from':previous_time_marker.strftime('%Y-%m-%d'),
            'performed_to':current_datetime.strftime('%Y-%m-%d')
        }

        res = self.client.get(INSIGHTS_EXPORT_SETS_URL, insights_payload)
        data = res.data.get('results', res.data.get('data', res.data))
        dt_object = datetime.fromisoformat(workout1.performed_at)
        performed_date_string = dt_object.date()

        self.assertEqual('/api/insightsexport_sets/?page=1&page_size=200',res.data.get('next'))
        self.assertFalse(res.data.get('previous'))
        self.assertEqual(2, len(data))
        self.assertEqual(data[0]['workout_id'], workout_2.id)
        self.assertEqual(data[0]['performed_at'], previous_time_marker.date().strftime('%Y-%m-%d'))
        self.assertEqual(data[0]['exercise_id'], exercise2.id)
        self.assertEqual(data[0]['exercise_name'], exercise2.name)
        self.assertEqual(data[0]['workout_exercise_id'], data_workout2_exercise_payload1['id'])
        self.assertEqual(data[0]['order'], data_workout2_exercise_payload1['order'])
        self.assertEqual(data[0]['set_id'], data_workout2_set_payload1['id'])
        self.assertEqual(data[0]['set_number'], data_workout2_set_payload1['set_number'])
        self.assertEqual(data[0]['reps'], data_workout2_set_payload1['reps'])
        self.assertEqual(data[0]['weight'], Decimal(data_workout2_set_payload1['weight']))

        self.assertEqual(data[1]['workout_id'], workout_2.id)
        self.assertEqual(data[1]['performed_at'], previous_time_marker.date().strftime('%Y-%m-%d'))
        self.assertEqual(data[1]['exercise_id'], exercise2.id)
        self.assertEqual(data[1]['exercise_name'], exercise2.name)
        self.assertEqual(data[1]['workout_exercise_id'], data_workout2_exercise_payload1['id'])
        self.assertEqual(data[1]['order'], data_workout2_exercise_payload1['order'])
        self.assertEqual(data[1]['set_id'], data_workout2_set_payload2['id'])
        self.assertEqual(data[1]['set_number'], data_workout2_set_payload2['set_number'])
        self.assertEqual(data[1]['reps'], data_workout2_set_payload2['reps'])
        self.assertEqual(data[1]['weight'], Decimal(data_workout2_set_payload2['weight']))
