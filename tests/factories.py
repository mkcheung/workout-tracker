
from django.contrib.auth import get_user_model
from django.utils import timezone
from exercises.models import (
    Exercise,
)
from workouts.models import (
    Workout,
    WorkoutExercise,
    WorkoutSet
)
User = get_user_model()

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

def create_workout(**params):
    current_datetime = timezone.now()
    defaults = {
        'notes':'Notes for the workout',
        'performed_at': current_datetime.isoformat()
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
