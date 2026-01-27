from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import InsightsExerciseSeriesViewSet

app_name = "insights"

urlpatterns = [
    path("exercise_series/", InsightsExerciseSeriesViewSet.as_view({'get':'list'}), name="exercise-series"),
    # path("/weekly_volume/", InsightsExerciseSeriesViewSet.as_view(), name="weekly_volume"),
    # path("/export_sets", InsightsExerciseSeriesViewSet.as_view(), name="export_sets")
]