from django.db import transaction
from django.shortcuts import get_object_or_404, render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions, filters, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .serializers import SetWorkoutExercisesAndSetsSerializer, WorkoutSerializer, WorkoutExerciseSerializer, WorkoutSetSerializer, WorkoutDetailSerializer
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
        serializer = SetWorkoutExercisesAndSetsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        submitted_items = serializer.validated_data["workout_exercises"]

        with transaction.atomic():
            WorkoutExercise.objects.filter(workout=workout).delete()

            created_workout_exercises = []

            for item in submitted_items:
                we = WorkoutExercise.objects.create(
                    workout=workout,
                    exercise_id=item["exercise_id"],
                    order=item["order"]
                )

                sets = item.get("sets", [])
                for set_item in sets:
                    WorkoutSet.objects.create(
                        workout_exercise=we,
                        set_number=set_item["set_number"],
                        reps=set_item["reps"],
                        weight=set_item.get("weight")
                    )

                created_workout_exercises.append(we)

        refreshed = WorkoutExercise.objects.filter(workout=workout).order_by("order")
        return Response(
            WorkoutExerciseSerializer(refreshed, many=True).data,
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