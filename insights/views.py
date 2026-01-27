from django.shortcuts import get_object_or_404, render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions, filters
from rest_framework.authentication import TokenAuthentication
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from workouts.models import Workout, WorkoutExercise, WorkoutSet
from .serializers import InsightsDateRangeQuerySerializer

class InsightsExerciseSeriesViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        user = request.user

        date_search_params = InsightsDateRangeQuerySerializer(data=request.query_params)
        date_search_params.is_valid(raise_exception=True)
        params = date_search_params.validated_data

        performed_from = params.get('performed_from')
        performed_to = params.get('performed_to')

        user_workouts = Workout.objects.filter(user=user)
        if params.get('exercise_id'):
            user_workouts = user_workouts.filter(
                workout_exercises__exercise_id = params.get('exercise_id')
            )
        
        user_workouts = user_workouts.prefetch_related('workout_exercises__workout_sets')
        
        if performed_from:
            user_workouts = user_workouts.filter(performed_at__date__gte=performed_from)

        if performed_to:
            user_workouts = user_workouts.filter(performed_at__date__lte=performed_to)

        return Response({
            'performed_from': str(performed_from) if performed_from else None,
            'performed_to': str(performed_to) if performed_to else None,
            'user_workouts': len(user_workouts)
        })


class InsightsWeeklyVolumeViewSet(viewsets.ViewSet):
    pass

class InsightsExportSetsViewSet(viewsets.ViewSet):
    pass