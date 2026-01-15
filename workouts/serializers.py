from rest_framework import serializers
from .models import Workout, WorkoutExercise, WorkoutSet
from exercises.models import Exercise

class WorkoutSerializer(serializers.ModelSerializer):
    class Meta: 
        model = Workout
        fields = ['id', 'notes', 'performed_at', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class WorkoutExerciseSerializer(serializers.ModelSerializer):
    workout = serializers.PrimaryKeyRelatedField(queryset=Workout.objects.none())
    exercise = serializers.PrimaryKeyRelatedField(queryset=Exercise.objects.all())
    class Meta:
        model = WorkoutExercise
        fields = ['id', "workout", "exercise", 'order', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return
        if request and not (request.user.is_staff or request.user.is_superuser):
            self.fields['workout'].queryset = Workout.objects.filter(user=request.user) 
        else:
            self.fields['workout'].queryset = Workout.objects.all()

    def validate_order(self, value):
        if value < 1:
            raise serializers.ValidationError("Order value must be greater or equal to 1.")
        return value

    def validate_workout(self, workout):
        request = self.context.get('request')
        if request and not (request.user.is_staff or request.user.is_superuser ):
            if workout.user_id != request.user.id:
                raise serializers.ValidationError('User does not have permission to modify this workout.')
        return workout

class WorkoutSetSerializer(serializers.ModelSerializer):
    workout_exercise = serializers.PrimaryKeyRelatedField(queryset=WorkoutExercise.objects.none())
    class Meta:
        model = WorkoutSet
        fields = ['id', 'workout_exercise', 'set_number', 'reps', 'weight', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return

        if request and not (request.user.is_staff or request.user.is_superuser):
            self.fields['workout_exercise'].queryset = WorkoutExercise.objects.filter(workout__user = request.user)
        else:
            self.fields['workout_exercise'].queryset = WorkoutExercise.objects.all()

    def validate_workout_exercise(self, workout_exercise):
        request = self.context.get('request')
        if request and not (request.user.is_staff or request.user.is_superuser):
            if workout_exercise.workout.user_id != request.user.id:
                raise serializers.ValidationError('User does not have permission to modify this workout set.')
        return workout_exercise

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
            raise serializers.ValidationError('Weight value must be greater or equal to 1 when provided.')
        return value