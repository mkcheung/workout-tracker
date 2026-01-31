from django.db.models import Prefetch
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404, render
from rest_framework import viewsets, permissions, filters
from rest_framework.authentication import TokenAuthentication
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from workouts.models import Workout, WorkoutExercise, WorkoutSet
from .serializers import InsightsDateRangeQuerySerializer, InsightsWeeklyVolumeSerializer
from .services import calculate_weekly_top_set, calculate_daily_1_rep_max, calculate_daily_tonnage, calculate_weekly_volume

class InsightsExerciseSeriesViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        user = request.user

        date_search_params = InsightsDateRangeQuerySerializer(data=request.query_params)
        date_search_params.is_valid(raise_exception=True)
        params = date_search_params.validated_data

        performed_from = params.get('performed_from')
        performed_to = params.get('performed_to')
        exercise_id = params.get('exercise_id')
        metric = params.get('metric')

        user_workouts = Workout.objects.filter(user=user, workout_exercises__exercise_id=params["exercise_id"]).prefetch_related(
            Prefetch(
                'workout_exercises',
                queryset = WorkoutExercise.objects
                    .filter(exercise_id=params['exercise_id'])
                    .prefetch_related('workout_sets')
            )
        )

        if performed_from:
            user_workouts = user_workouts.filter(performed_at__date__gte=performed_from)
        if performed_to:
            user_workouts = user_workouts.filter(performed_at__date__lte=performed_to)
        
        if metric == 'top_set_weight':
            top_set_weight_response = calculate_weekly_top_set(user_workouts, performed_from, performed_to, params.get('exercise_id'))
            return Response(top_set_weight_response)
        elif metric == 'estimated_1rm':
            estimated_1_rep_max_response = calculate_daily_1_rep_max(user_workouts, performed_from, performed_to, params.get('exercise_id'))
            return Response(estimated_1_rep_max_response)
        elif metric == 'tonnage':
            daily_tonnage_response = calculate_daily_tonnage(user_workouts, performed_from, performed_to, params.get('exercise_id'))
            return Response(daily_tonnage_response)
            
        return Response({'message': 'Unsupported Metric'}, 400)


class InsightsWeeklyVolumeViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        user = request.user
        weekly_volume_params = InsightsWeeklyVolumeSerializer(data=request.query_params)
        weekly_volume_params.is_valid(raise_exception=True)
        params = weekly_volume_params.validated_data

        exercise_id = params.get('exercise_id')
        weeks = params.get('weeks')
        to = params.get('to')

        user_workouts = Workout.objects.filter(user=user, workout_exercises__exercise_id = exercise_id).prefetch_related(
            Prefetch(
                'workout_exercises',
                queryset = WorkoutExercise.objects.filter(exercise_id=params['exercise_id'])
                .prefetch_related('workout_sets')
            )
        )
        print('calculate_weekly_volume')
        temp = calculate_weekly_volume(user_workouts, weeks, to, exercise_id)
        return Response(temp)
        

class InsightsExportSetsViewSet(viewsets.ViewSet):
    pass