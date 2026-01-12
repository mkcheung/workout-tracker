from rest_framework import serializers
from .models import Exercise

class ExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        fields = ['id', 'name', 'category', 'muscle_group', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'is_active', 'created_at', 'updated_at']

    def valiidate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Exercise Name cannnot be empty.")
        return value