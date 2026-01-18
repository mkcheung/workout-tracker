from rest_framework.routers import DefaultRouter
from .views import WorkoutViewSet, WorkoutExerciseViewSet, WorkoutSetViewSet

app_name = "workouts"

router = DefaultRouter()
router.register('workouts', WorkoutViewSet, basename='workouts')
router.register('workout-exercises', WorkoutExerciseViewSet, basename='workout-exercises')
router.register('workout-sets', WorkoutSetViewSet, basename='workout-sets') 

urlpatterns = router.urls