from django.shortcuts import render
from rest_framework import viewsets, permissions, filters
from .serializers import ExerciseSerializer

class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permission.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)

class ExerciseViewSet(viewsets.ModelViewSet):
    serializer = ExerciseSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ["name", "category", "muscle_group"]
    ordering = ["name"]

    def get_queryset(self):
        qs = Exercise.objects.all()
        if not (self.request.user and self.request.user.is_staff):
            qs = qs.filter(is_active=True)
        return qs
