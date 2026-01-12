from django.db import models

class Exercise(models.Model):
    class Category(models.TextChoices):
        PUSH = "push", "Push"
        PULL = "pull", "Pull"
        STRENGTH = "strength", "Strength"
        CARDIO = "cardio", "Cardio"
        
    class MuscleGroup(models.TextChoices):
        CHEST = "chest", "Chest"
        BACK = "back", "Back"
        LEGS = "legs", "Legs"

    name = models.CharField(
        max_length = 100,
        db_index=True,
        unique=True
    )

    category = models.CharField(
        max_length = 20,
        choices = Category.choices,
        blank = True,
        null = True
    )

    muscle_group = models.CharField(
        max_length = 40,
        choices = MuscleGroup.choices,
        blank = True,
        null = True
    )

    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name