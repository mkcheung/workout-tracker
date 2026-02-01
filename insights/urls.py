from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import InsightsExerciseSeriesViewSet, InsightsWeeklyVolumeViewSet

app_name = "insights"

urlpatterns = [
    path("exercise_series/", InsightsExerciseSeriesViewSet.as_view({'get':'list'}), name="exercise-series"),
    path("weekly_volume/", InsightsWeeklyVolumeViewSet.as_view({'get':'list'}), name="weekly-volume"),
    path("export_sets/", InsightsExerciseSeriesViewSet.as_view({'get':'list'}), name="export-sets")
]