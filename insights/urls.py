from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import InsightsExerciseSeriesViewSet, InsightsWeeklyVolumeViewSet, InsightsExportSetsViewSet

app_name = "insights"

urlpatterns = [
    path("exercise-series/", InsightsExerciseSeriesViewSet.as_view({'get':'list'}), name="exercise-series"),
    path("weekly-volume/", InsightsWeeklyVolumeViewSet.as_view({'get':'list'}), name="weekly-volume"),
    path("export-sets/", InsightsExportSetsViewSet.as_view({'get':'list'}), name="export-sets"),
]