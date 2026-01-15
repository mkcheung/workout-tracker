from rest_framework.routers import DefaultRouter
from .views import WorkoutViewSet, WorkoutExerciseViewSet, WorkoutSetViewSet

app_name = "workouts"

router = DefaultRouter()
router.register('workouts', WorkoutViewSet)
router.register('workout-exercises', WorkoutExerciseViewSet)
router.register('workout-sets', WorkoutSetViewSet) 

urlpatterns = router.urls