from django.db import models
from django.conf import settings
from django.utils import timezone


class Workout(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="workouts",
        db_index=True,
    )
    notes = models.TextField(blank=True)
    performed_at = models.DateTimeField(
        default=timezone.now,
        db_index=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Workout {self.id}"

class WorkoutExercise(models.Model):

    workout = models.ForeignKey(
        "workouts.Workout", on_delete=models.CASCADE, related_name="workout_exercises"
    )

    exercise = models.ForeignKey(
        "exercises.Exercise", on_delete=models.CASCADE, related_name="workout_exercises"
    )

    order = models.PositiveSmallIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(
                fields=["workout", "order"],
                name="uniq_workoutexercise_order_per_workout",
            ),
        ]

    def __str__(self) -> str:
        return f"WorkoutExercise {self.id}"

class WorkoutSet(models.Model):
    workout_exercise = models.ForeignKey(
        "workouts.WorkoutExercise", on_delete=models.CASCADE, related_name="workout_sets"
    )
    set_number = models.PositiveSmallIntegerField()
    reps = models.PositiveSmallIntegerField()
    weight = models.DecimalField(
        max_digits=6, decimal_places=2, blank=True, null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["set_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["workout_exercise", "set_number"],
                name="uniq_set_number_per_workout_exercise",
            ),
        ]
    
    def __str__(self) -> str:
        return f"WorkoutSet {self.id}"