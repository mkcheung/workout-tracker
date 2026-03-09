"""
Management command: seed_demo

Creates a demo user with ~3 months of realistic workout data so the
Progress page charts have something interesting to display.

Usage:
    python manage.py seed_demo
    python manage.py seed_demo --email demo@example.com --password demo1234
    python manage.py seed_demo --flush   # wipe existing demo data first
"""

import random
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from exercises.models import Exercise
from workouts.models import Workout, WorkoutExercise, WorkoutSet

User = get_user_model()

# ---------------------------------------------------------------------------
# Exercise definitions
# Each entry: (name, category, muscle_group, start_weight, weekly_gain, sets)
# start_weight = lbs on week 1
# weekly_gain  = avg lbs added per week (realistic progressive overload)
# sets         = list of (reps, weight_fraction) — weight_fraction relative to top set
# ---------------------------------------------------------------------------
EXERCISE_PLANS = [
    {
        "name": "Barbell Bench Press",
        "category": "push",
        "muscle_group": "chest",
        "start_weight": 135,
        "weekly_gain": 2.5,
        "sets": [
            (5, 0.75),   # warm-up
            (5, 0.90),
            (3, 1.00),   # top set
            (5, 0.90),
            (8, 0.80),
        ],
    },
    {
        "name": "Barbell Back Squat",
        "category": "strength",
        "muscle_group": "legs",
        "start_weight": 185,
        "weekly_gain": 5.0,
        "sets": [
            (5, 0.70),
            (5, 0.85),
            (3, 1.00),
            (5, 0.85),
            (8, 0.75),
        ],
    },
    {
        "name": "Deadlift",
        "category": "pull",
        "muscle_group": "back",
        "start_weight": 225,
        "weekly_gain": 5.0,
        "sets": [
            (5, 0.70),
            (3, 0.90),
            (1, 1.00),   # heavy single
            (3, 0.90),
            (5, 0.80),
        ],
    },
    {
        "name": "Overhead Press",
        "category": "push",
        "muscle_group": "chest",
        "start_weight": 85,
        "weekly_gain": 1.25,
        "sets": [
            (5, 0.80),
            (5, 0.90),
            (5, 1.00),
            (8, 0.85),
        ],
    },
    {
        "name": "Barbell Row",
        "category": "pull",
        "muscle_group": "back",
        "start_weight": 115,
        "weekly_gain": 2.5,
        "sets": [
            (8, 0.85),
            (8, 0.90),
            (8, 1.00),
            (10, 0.85),
        ],
    },
]

# Which exercises appear on which day of a 3-day-per-week programme
# Day A: Squat / Bench / Row
# Day B: Squat / OHP   / Deadlift
PROGRAMMES = {
    "A": ["Barbell Back Squat", "Barbell Bench Press", "Barbell Row"],
    "B": ["Barbell Back Squat", "Overhead Press", "Deadlift"],
}

# Workout schedule: Mon / Wed / Fri, alternating A / B
WORKOUT_DAYS = [0, 2, 4]  # weekday indices


def _round5(value: float) -> Decimal:
    """Round to nearest 5 lbs (standard plate increments)."""
    return Decimal(str(round(round(value / 5) * 5, 2)))


def _week_number(d: date, start: date) -> int:
    return (d - start).days // 7


class Command(BaseCommand):
    help = "Seed a demo user with 3 months of progressive workout data."

    def add_arguments(self, parser):
        parser.add_argument("--email", default="demo@example.com")
        parser.add_argument("--password", default="demo1234")
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete existing workouts for the demo user before seeding.",
        )
        parser.add_argument(
            "--weeks",
            type=int,
            default=13,
            help="Number of weeks of data to generate (default 13 ≈ 3 months).",
        )

    def handle(self, *args, **options):
        email = options["email"]
        password = options["password"]
        num_weeks = options["weeks"]

        # ------------------------------------------------------------------
        # 1. Get or create the demo user
        # ------------------------------------------------------------------
        user, created = User.objects.get_or_create(
            email=email,
            defaults={"username": email, "first_name": "Demo", "last_name": "User"},
        )
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Created user: {email}"))
        else:
            self.stdout.write(f"Using existing user: {email}")

        if options["flush"]:
            deleted, _ = Workout.objects.filter(user=user).delete()
            self.stdout.write(self.style.WARNING(f"Flushed {deleted} existing workouts."))

        # ------------------------------------------------------------------
        # 2. Get or create exercises
        # ------------------------------------------------------------------
        exercise_map = {}
        for plan in EXERCISE_PLANS:
            exercise, _ = Exercise.objects.get_or_create(
                name=plan["name"],
                defaults={
                    "category": plan["category"],
                    "muscle_group": plan["muscle_group"],
                },
            )
            exercise_map[plan["name"]] = exercise
        self.stdout.write(f"Exercises ready: {list(exercise_map.keys())}")

        # Build a lookup from exercise name → plan dict
        plan_map = {p["name"]: p for p in EXERCISE_PLANS}

        # ------------------------------------------------------------------
        # 3. Build the workout schedule
        # ------------------------------------------------------------------
        # Start from the Monday 13 weeks ago
        today = date.today()
        start_monday = today - timedelta(weeks=num_weeks) - timedelta(days=today.weekday())

        workout_dates = []
        programme_cycle = ["A", "B"]
        cycle_index = 0

        current = start_monday
        end = today
        while current <= end:
            if current.weekday() in WORKOUT_DAYS:
                label = programme_cycle[cycle_index % 2]
                workout_dates.append((current, label))
                cycle_index += 1
            current += timedelta(days=1)

        # ------------------------------------------------------------------
        # 4. Create workouts
        # ------------------------------------------------------------------
        workouts_created = 0
        for workout_date, programme_label in workout_dates:
            week = _week_number(workout_date, start_monday)

            # Skip if a workout already exists on this date for this user
            performed_dt = timezone.make_aware(
                timezone.datetime(workout_date.year, workout_date.month, workout_date.day, 10, 0)
            )
            if Workout.objects.filter(user=user, performed_at__date=workout_date).exists():
                continue

            workout = Workout.objects.create(user=user, performed_at=performed_dt)

            exercise_names = PROGRAMMES[programme_label]
            for order, ex_name in enumerate(exercise_names, start=1):
                exercise = exercise_map[ex_name]
                plan = plan_map[ex_name]

                we = WorkoutExercise.objects.create(
                    workout=workout,
                    exercise=exercise,
                    order=order,
                )

                top_weight = plan["start_weight"] + (week * plan["weekly_gain"])
                # Add small random noise (+/- 2.5 lbs) to make it feel natural
                top_weight += random.choice([-2.5, 0, 0, 2.5])

                for set_num, (reps, fraction) in enumerate(plan["sets"], start=1):
                    weight = _round5(top_weight * fraction)
                    WorkoutSet.objects.create(
                        workout_exercise=we,
                        set_number=set_num,
                        reps=reps,
                        weight=weight,
                    )

            workouts_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone! Created {workouts_created} workouts over {num_weeks} weeks.\n"
                f"\n  Email:    {email}"
                f"\n  Password: {password}\n"
                f"\nTo view the data, log in on the frontend and visit the Progress page.\n"
                f"Try these exercises with any metric (top_set_weight, estimated_1rm, tonnage):\n"
            )
        )
        for name in exercise_map:
            self.stdout.write(f"  • {name}")
