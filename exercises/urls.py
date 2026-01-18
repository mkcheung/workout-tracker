from rest_framework.routers import DefaultRouter
from .views import ExerciseViewSet

app_name = "exercises"

router = DefaultRouter()
router.register("exercises", ExerciseViewSet, basename="exercise")

urlpatterns = router.urls