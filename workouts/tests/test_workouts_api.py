
from exercises.models import (
    Exercise,
)
from datetime import datetime
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.test import APITestCase
from workouts.models import (
    Workout,
    WorkoutExercise,
    WorkoutSet
)

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

def create_user(**params):
    defaults = {
        'username': 'test@example.com',
        'email': 'test@example.com',
        'password': 'test@123',
        'first_name': 'test',
        'last_name': 'last'
    }
    defaults.update(**params)
    password = defaults.pop('password')
    user = User.objects.create_user(defaults);
    user.set_password(password)
    user.save()
    return user

def create_admin_user(**params):
    defaults = {
        'username': 'testadmin@example.com',
        'email': 'testadmin@example.com',
        'password': 'test@123'
    }
    defaults.update(**params)
    password = defaults.pop('password')
    admin_user = User.objects.create_superuser(defaults)
    admin_user.set_password(password)
    return admin_user

def create_workout(**params):
    defaults = {
        'notes': 'workout default'
    }
    defaults.update(**params)
    workout = Workout.objects.create(**defaults)
    return workout

def create_exercise(**params):
    defaults = {
        'name': 'an exercise',
        'category': 'push',
        'muscle_group': 'chest'
    }
    defaults.update(**params)
    exercise = Exercise.objects.create(**defaults)
    return exercise

class PublicAuthApiTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
    
    def test_unauthenticated_access(self):
        res = self.client.get(WORKOUT_URL)
        self.assertIn(res.status_code, [status.HTTP_401_UNAUTHORIZED])

class PrivateAuthApiTests(APITestCase):
    def setUp(self):
        self.admin_user = create_admin_user()
        self.user = create_user()
        self.client = APIClient()

    def test_create_workout(self):
        self.client.force_authenticate(self.user)
        current_datetime = timezone.now()
        payload = {
            'notes':'Notes for the workout',
            'performed_at': current_datetime.isoformat()
        }
        res = self.client.post(WORKOUT_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['notes'], payload['notes'])
        self.assertEqual(res.data['performed_at'], payload["performed_at"].replace("+00:00", "Z"))

    def test_update_workout(self):
        self.client.force_authenticate(self.user)
        created_datetime = timezone.now()
        workout_payload = {
            'notes':'before update',
            'performed_at': created_datetime.isoformat()
        }
        res_workout = self.client.post(WORKOUT_URL, workout_payload)
        self.assertEqual(res_workout.status_code, status.HTTP_201_CREATED)
        data = res_workout.data.get('results', res_workout.data.get('data', res_workout.data))
        workout_update_payload = {
            'notes':'after update'
        }
        res = self.client.patch(default_workout_url(data['id']), workout_update_payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data_post_update = res.data.get('results', res.data.get('data', res.data))
        self.assertEqual(data_post_update['notes'], workout_update_payload['notes'])
    
    def test_delete_workout(self):
        self.client.force_authenticate(self.user);
        created_datetime = timezone.now()
        payload={
            'notes':'test deletion',
            'performed_at': created_datetime.isoformat()
        }
        res_workout = self.client.post(WORKOUT_URL, payload)
        self.assertEqual(res_workout.status_code, status.HTTP_201_CREATED)
        res_workout_data = res_workout.data.get('results', res_workout.data.get('data', res_workout.data))

        res = self.client.delete(default_workout_url(res_workout_data['id']))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Workout.objects.filter(id=res_workout_data['id']).exists())

    def test_create_workout_exercise(self):
        self.client.force_authenticate(self.user)
        current_datetime = timezone.now()
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

    def test_add_multiple_workout_exercise(self):
        self.client.force_authenticate(self.user)
        current_datetime = timezone.now()
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

        exercise_payload_2 = {
            'name': 'an additional exercise',
            'category': 'pull',
            'muscle_group': 'legs'
        }
        exercise2 = create_exercise(**exercise_payload_2)
        update_workout_exercise_payload = {
            'workout': workout.id,
            'exercise': exercise2.id,
            'order':2
        }
        res_workout_exercise_update = self.client.post(WORKOUT_EXERCISE_URL, update_workout_exercise_payload)
        data_from_2nd_update = res_workout_exercise_update.data.get('results', res_workout_exercise_update.data.get('data', res_workout_exercise_update.data))
        self.assertEqual(workout.id, data_from_2nd_update['workout'])
        self.assertEqual(exercise2.id, data_from_2nd_update['exercise'])
        self.assertEqual(update_workout_exercise_payload['order'], data_from_2nd_update['order'])

        related_workout_exercises = WorkoutExercise.objects.filter(workout=workout.id)
        self.assertEqual(len(related_workout_exercises), 2)

        expected = {(workout_exercise_payload['exercise'], workout_exercise_payload['order']),(update_workout_exercise_payload['exercise'], update_workout_exercise_payload['order'])}
        actual = set(
            WorkoutExercise.objects.filter(workout=workout.id)
            .values_list("exercise_id", "order")
        )
        self.assertEqual(actual, expected)
        
    def test_update_workout_exercise(self):
        self.client.force_authenticate(self.user)
        current_datetime = timezone.now()
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

        exercise_payload_2 = {
            'name': 'an additional exercise',
            'category': 'pull',
            'muscle_group': 'legs'
        }
        exercise2 = create_exercise(**exercise_payload_2)
        workout_update_payload = {
            'exercise':exercise2.id,
            'order':4
        }
        res_from_update = self.client.patch(default_workout_exercise_url(data['id']), workout_update_payload)

        data = res_from_update.data.get('results', res_from_update.data.get('data', res_from_update.data))
        self.assertEqual(workout.id, data['workout'])
        self.assertEqual(exercise2.id, data['exercise'])
        self.assertEqual(workout_update_payload['order'], data['order'])
        
    def test_delete_workout_exercise(self):
        self.client.force_authenticate(self.user)
        current_datetime = timezone.now()
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
        data_workout_exercise = res.data.get('results', res.data.get('data', res.data))
        self.assertEqual(workout.id, data_workout_exercise['workout'])
        self.assertEqual(exercise.id, data_workout_exercise['exercise'])
        self.assertEqual(workout_exercise_payload['order'], data_workout_exercise['order'])

        res_workout_exercise = self.client.delete(default_workout_exercise_url(data_workout_exercise['id']))
        self.assertEqual(res_workout_exercise.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(WorkoutExercise.objects.filter(id=data_workout_exercise['id']).exists())

    def test_create_workout_set(self):
        self.client.force_authenticate(self.user)
        current_datetime = timezone.now()
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

    def test_update_workout_set(self):
        self.client.force_authenticate(self.user)
        current_datetime = timezone.now()
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

        workout_set_update_payload = {
            'reps':12,
        }
        res_from_update = self.client.patch(default_workout_set_url(data['id']), workout_set_update_payload)
        data = res_from_update.data.get('results', res_from_update.data.get('data', res_from_update.data))
        self.assertEqual(workout_set_update_payload['reps'], data['reps'])

    def test_delete_workout_set(self):
        self.client.force_authenticate(self.user)
        current_datetime = timezone.now()
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

        res_from_update = self.client.delete(default_workout_set_url(data['id']))
        self.assertEqual(res_from_update.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(WorkoutSet.objects.filter(id=data['id']).exists())