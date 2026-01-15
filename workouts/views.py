from django.shortcuts import render
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
    filter_backends = [DjangoFilterBackend, SearchFilter]

    def perform_create(self):
        serializer.save(self.request.user)


class WorkoutExerciseViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend, SearchFilter]
    permission_classes = [IsAuthenticated]
    serializer_class = WorkoutExerciseSerializer

    def perform_create(self):
        serializer.save(self.request.user)

class WorkoutSetViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend, SearchFilter]
    permission_classes = [IsAuthenticated]
    serializer_class = WorkoutSetSerializer

    def perform_create(self):
        serializer.save(self.request.user)