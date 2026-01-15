from django.shortcuts import get_object_or_404, render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions, filters
from rest_framework.authentication import TokenAuthentication
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import WorkoutSerializer, WorkoutExerciseSerializer, WorkoutSetSerializer
from .models import Workout, WorkoutExercise, WorkoutSet

class WorkoutViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend, SearchFilter]
    permission_classes = [IsAuthenticated]
    serializer_class = WorkoutSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Workout.objects.all()
        return Workout.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class WorkoutExerciseViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend, SearchFilter]
    permission_classes = [IsAuthenticated]
    serializer_class = WorkoutExerciseSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return WorkoutExercise.objects.all()
        return WorkoutExercise.objects.filter(workout__user = self.request.user)

    def perform_create(self, serializer):
        serializer.save()

class WorkoutSetViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend, SearchFilter]
    permission_classes = [IsAuthenticated]
    serializer_class = WorkoutSetSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return WorkoutSet.objects.all()
        return WorkoutSet.objects.filter(workout_exercise__workout__user = self.request.user)

    def perform_create(self, serializer):
        serializer.save()