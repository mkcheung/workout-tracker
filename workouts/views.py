from django.db import transaction
from django.shortcuts import get_object_or_404, render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions, filters, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .serializers import SetWorkoutExercisesSerializer, WorkoutSerializer, WorkoutExerciseSerializer, WorkoutSetSerializer, WorkoutDetailSerializer
from .models import Workout, WorkoutExercise, WorkoutSet

class WorkoutViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        'performed_at': ['date', 'gte', 'lte'],
        'created_at': ['gte', 'lte']
    }
    search_fields = ['notes']
    ordering_fields = ['performed_at', 'created_at', 'updated_at']
    ordering = ['-performed_at']
    permission_classes = [IsAuthenticated]
    serializer_class = WorkoutSerializer
    queryset = Workout.objects.all()

    def get_serializer_class(self):
        if self.action in ['retrieve', 'list']:
            return WorkoutDetailSerializer
        return WorkoutSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Workout.objects.all()
        return Workout.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["put"], url_path="set-exercises")
    def set_exercises(self, request, pk=None):
        workout = self.get_object()
        req = SetWorkoutExercisesSerializer(data=request.data, context={"request":request})
        req.is_valid(raise_exception=True)
        exercise_ids = req.validated_data['exercise_ids']

        with transaction.atomic():
            WorkoutExercise.objects.filter(workout=workout).delete()

            rows = [
                WorkoutExercise(workout=workout, exercise_id=ex_id, order = i + 1)
                for i, ex_id in enumerate(exercise_ids)
            ]
            if rows:
                WorkoutExercise.objects.bulk_create(rows)
        
        new_qs = WorkoutExercise.objects.filter(workout=workout).order_by('order')
        return Response(
            WorkoutExerciseSerializer(new_qs, many=True, context={"request":request}).data,
            status=status.HTTP_200_OK
        )



class WorkoutExerciseViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['workout', 'exercise']
    ordering_fields = ['created_at', 'order']
    permission_classes = [IsAuthenticated]
    serializer_class = WorkoutExerciseSerializer
    queryset = WorkoutExercise.objects.all()
    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return WorkoutExercise.objects.all()
        return WorkoutExercise.objects.filter(workout__user = self.request.user)

    def perform_create(self, serializer):
        serializer.save()

class WorkoutSetViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['workout_exercise']
    ordering_fields = ['set_number', 'created_at', 'updated_at']
    ordering = ['set_number']
    permission_classes = [IsAuthenticated]
    serializer_class = WorkoutSetSerializer
    queryset = WorkoutSet.objects.all()

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return WorkoutSet.objects.all()
        return WorkoutSet.objects.filter(workout_exercise__workout__user = self.request.user)

    def perform_create(self, serializer):
        serializer.save()