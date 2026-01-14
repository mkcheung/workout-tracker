from rest_framework import serializers
from .models import Workout, WorkoutExercise, WorkoutSet
from exercises.models import Exercise

class WorkoutSerializer(serializers.ModelSerializer):
    class Meta: 
        model = Workout
        fields = ['id', 'notes', 'performed_at', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class WorkoutExerciseSerializer(serializers.ModelSerializer):
    workout = serializers.PrimaryKeyRelatedField(read_only=True)
    exercise = serializers.PrimaryKeyRelatedField(queryset=Exercise.objects.all())
    class Meta:
        model = WorkoutExercise
        fields = ['id', "workout", "exercise", 'order', 'created_at', 'updated_at']
        read_only_fields = ['id', "workout", 'created_at', 'updated_at']

    def validate_order(self, value):
        if value < 1:
            raise serializers.ValidationError("Order value must be greater or equal to 1.")
        return value

    def create(self, validated_data):
        workout = self.context.get('workout')
        if workout is None:
            raise AssertionError("Workout needed in the serializer context.")
        return WorkoutExercise.objects.create(workout=workout, **validated_data)


class WorkoutSetSerializer(serializers.ModelSerializer):
    workout_exercise = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = WorkoutSet
        fields = ['id', 'workout_exercise', 'set_number', 'reps', 'weight', 'created_at', 'updated_at']
        read_only_fields = ['id', 'workout_exercise', 'created_at', 'updated_at']

    def validate_set_number(self, value):
        if value < 1:
            raise serializers.ValidationError('Set numbers must be greater or equal to 1.')
        return value
    def validate_reps(self, value):
        if value < 1:
            raise serializers.ValidationError('Rep numbers must be greater or equal to 1.')
        return value
    def validate_weight(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError('Rep numbers must be greater or equal to 1 when provided.')
        return value

    def create(self, validated_data):
        workout_exercise = self.context.get("workout_exercise")
        if workout_exercise is None:
            raise AssertionError("Workout Exercuse needed in the serializer context.")
        return WorkoutSet.objects.create(workout_exercise=workout_exercise,  **validated_data)
