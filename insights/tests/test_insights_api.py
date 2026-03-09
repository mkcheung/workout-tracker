from datetime import date, datetime, timedelta, timezone as dt_timezone
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from workouts.models import Workout, WorkoutExercise, WorkoutSet
from tests.factories import create_user, create_workout, create_exercise

User = get_user_model()

EXERCISE_SERIES_URL = reverse("insights:exercise-series")
WEEKLY_VOLUME_URL = reverse("insights:weekly-volume")
EXPORT_SETS_URL = reverse("insights:export-sets")


def make_workout(user, performed_at, exercise, sets):
    """
    Helper: create a Workout with one WorkoutExercise and the given sets.
    `sets` is a list of (weight, reps) tuples. Pass weight=None to simulate
    a set with no weight recorded.
    """
    workout = Workout.objects.create(user=user, performed_at=performed_at)
    we = WorkoutExercise.objects.create(workout=workout, exercise=exercise, order=1)
    for i, (weight, reps) in enumerate(sets, start=1):
        WorkoutSet.objects.create(
            workout_exercise=we,
            set_number=i,
            reps=reps,
            weight=weight,
        )
    return workout


# ---------------------------------------------------------------------------
# Authentication guard
# ---------------------------------------------------------------------------

class InsightsAuthTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.exercise = create_exercise()

    def test_exercise_series_requires_auth(self):
        res = self.client.get(EXERCISE_SERIES_URL, {
            "exercise_id": self.exercise.id,
            "metric": "top_set_weight",
        })
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_weekly_volume_requires_auth(self):
        res = self.client.get(WEEKLY_VOLUME_URL, {"exercise_id": self.exercise.id})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_export_sets_requires_auth(self):
        res = self.client.get(EXPORT_SETS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# Exercise series — top_set_weight
# ---------------------------------------------------------------------------

class TopSetWeightTests(APITestCase):
    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.exercise = create_exercise()

    def _get(self, extra=None):
        params = {
            "exercise_id": self.exercise.id,
            "metric": "top_set_weight",
            "performed_from": "2026-01-01",
            "performed_to": "2026-12-31",
        }
        if extra:
            params.update(extra)
        return self.client.get(EXERCISE_SERIES_URL, params)

    def test_returns_200_with_data(self):
        make_workout(self.user, datetime(2026, 2, 1, tzinfo=dt_timezone.utc),
                     self.exercise, [(Decimal("100"), 5)])
        res = self._get()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["metric"], "top_set_weight")
        self.assertEqual(res.data["exercise_id"], self.exercise.id)

    def test_picks_heaviest_set_per_day(self):
        make_workout(self.user, datetime(2026, 2, 1, tzinfo=dt_timezone.utc),
                     self.exercise, [(Decimal("80"), 5), (Decimal("100"), 3), (Decimal("90"), 4)])
        res = self._get()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["points"]), 1)
        self.assertEqual(res.data["points"][0]["value"], 100.0)

    def test_skips_sets_with_null_weight(self):
        make_workout(self.user, datetime(2026, 2, 1, tzinfo=dt_timezone.utc),
                     self.exercise, [(None, 5)])
        res = self._get()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["points"], [])
        self.assertIsNone(res.data["summary"]["start"])

    def test_summary_single_day(self):
        make_workout(self.user, datetime(2026, 2, 1, tzinfo=dt_timezone.utc),
                     self.exercise, [(Decimal("100"), 5)])
        res = self._get()
        summary = res.data["summary"]
        self.assertEqual(summary["start"], 100.0)
        self.assertEqual(summary["latest"], 100.0)
        self.assertEqual(summary["change"], 0.0)

    def test_summary_multiple_days(self):
        make_workout(self.user, datetime(2026, 2, 1, tzinfo=dt_timezone.utc),
                     self.exercise, [(Decimal("100"), 5)])
        make_workout(self.user, datetime(2026, 3, 1, tzinfo=dt_timezone.utc),
                     self.exercise, [(Decimal("120"), 5)])
        res = self._get()
        summary = res.data["summary"]
        self.assertEqual(summary["start"], 100.0)
        self.assertEqual(summary["latest"], 120.0)
        self.assertEqual(summary["change"], 20.0)

    def test_only_returns_data_for_requested_exercise(self):
        other_exercise = create_exercise(name="other exercise")
        make_workout(self.user, datetime(2026, 2, 1, tzinfo=dt_timezone.utc),
                     other_exercise, [(Decimal("200"), 5)])
        res = self._get()
        self.assertEqual(res.data["points"], [])

    def test_date_filtering_excludes_out_of_range(self):
        make_workout(self.user, datetime(2025, 6, 1, tzinfo=dt_timezone.utc),
                     self.exercise, [(Decimal("100"), 5)])
        res = self._get()  # range is 2026
        self.assertEqual(res.data["points"], [])

    def test_other_user_data_not_included(self):
        other_user = create_user(username="other@example.com", email="other@example.com")
        make_workout(other_user, datetime(2026, 2, 1, tzinfo=dt_timezone.utc),
                     self.exercise, [(Decimal("200"), 5)])
        res = self._get()
        self.assertEqual(res.data["points"], [])

    def test_missing_exercise_id_returns_400(self):
        res = self.client.get(EXERCISE_SERIES_URL, {"metric": "top_set_weight"})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_metric_returns_400(self):
        res = self.client.get(EXERCISE_SERIES_URL, {
            "exercise_id": self.exercise.id,
            "metric": "nonsense",
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_performed_from_after_performed_to_returns_400(self):
        res = self.client.get(EXERCISE_SERIES_URL, {
            "exercise_id": self.exercise.id,
            "metric": "top_set_weight",
            "performed_from": "2026-12-31",
            "performed_to": "2026-01-01",
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# Exercise series — estimated_1rm
# ---------------------------------------------------------------------------

class Estimated1RMTests(APITestCase):
    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.exercise = create_exercise()

    def _get(self, extra=None):
        params = {
            "exercise_id": self.exercise.id,
            "metric": "estimated_1rm",
            "performed_from": "2026-01-01",
            "performed_to": "2026-12-31",
        }
        if extra:
            params.update(extra)
        return self.client.get(EXERCISE_SERIES_URL, params)

    def test_returns_200_with_correct_metric(self):
        make_workout(self.user, datetime(2026, 2, 1, tzinfo=dt_timezone.utc),
                     self.exercise, [(Decimal("100"), 10)])
        res = self._get()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["metric"], "estimated_1rm")

    def test_1rm_formula(self):
        # Epley: weight * (1 + reps/30)
        # 100 * (1 + 10/30) = 100 * 1.333... = 133.33
        make_workout(self.user, datetime(2026, 2, 1, tzinfo=dt_timezone.utc),
                     self.exercise, [(Decimal("100"), 10)])
        res = self._get()
        self.assertEqual(len(res.data["points"]), 1)
        self.assertAlmostEqual(res.data["points"][0]["value"], 133.33, places=1)

    def test_picks_best_1rm_per_day(self):
        # set 1: 100 * (1 + 10/30) = 133.33
        # set 2: 80  * (1 + 20/30) = 133.33  — tie; either is fine
        # set 3: 120 * (1 + 5/30)  = 140.0   — winner
        make_workout(self.user, datetime(2026, 2, 1, tzinfo=dt_timezone.utc),
                     self.exercise, [
                         (Decimal("100"), 10),
                         (Decimal("80"), 20),
                         (Decimal("120"), 5),
                     ])
        res = self._get()
        self.assertEqual(len(res.data["points"]), 1)
        self.assertAlmostEqual(res.data["points"][0]["value"], 140.0, places=1)

    def test_skips_null_weight_sets(self):
        make_workout(self.user, datetime(2026, 2, 1, tzinfo=dt_timezone.utc),
                     self.exercise, [(None, 10)])
        res = self._get()
        self.assertEqual(res.data["points"], [])
        self.assertIsNone(res.data["summary"]["start"])

    def test_skips_zero_reps_sets(self):
        make_workout(self.user, datetime(2026, 2, 1, tzinfo=dt_timezone.utc),
                     self.exercise, [(Decimal("100"), 0)])
        res = self._get()
        self.assertEqual(res.data["points"], [])

    def test_summary_multiple_days(self):
        make_workout(self.user, datetime(2026, 2, 1, tzinfo=dt_timezone.utc),
                     self.exercise, [(Decimal("100"), 10)])
        make_workout(self.user, datetime(2026, 3, 1, tzinfo=dt_timezone.utc),
                     self.exercise, [(Decimal("100"), 20)])
        res = self._get()
        # day1: 100*(1+10/30)=133.33, day2: 100*(1+20/30)=166.67
        self.assertEqual(len(res.data["points"]), 2)
        self.assertAlmostEqual(res.data["summary"]["start"], 133.33, places=1)
        self.assertAlmostEqual(res.data["summary"]["latest"], 166.67, places=1)


# ---------------------------------------------------------------------------
# Exercise series — tonnage
# ---------------------------------------------------------------------------

class DailyTonnageTests(APITestCase):
    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.exercise = create_exercise()

    def _get(self, extra=None):
        params = {
            "exercise_id": self.exercise.id,
            "metric": "tonnage",
            "performed_from": "2026-01-01",
            "performed_to": "2026-12-31",
        }
        if extra:
            params.update(extra)
        return self.client.get(EXERCISE_SERIES_URL, params)

    def test_returns_200_with_correct_metric(self):
        make_workout(self.user, datetime(2026, 2, 1, tzinfo=dt_timezone.utc),
                     self.exercise, [(Decimal("100"), 5)])
        res = self._get()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["metric"], "tonnage")

    def test_sums_all_sets(self):
        # 3 sets: 100*5 + 80*8 + 60*10 = 500+640+600 = 1740
        make_workout(self.user, datetime(2026, 2, 1, tzinfo=dt_timezone.utc),
                     self.exercise, [
                         (Decimal("100"), 5),
                         (Decimal("80"), 8),
                         (Decimal("60"), 10),
                     ])
        res = self._get()
        self.assertEqual(len(res.data["points"]), 1)
        self.assertAlmostEqual(res.data["points"][0]["value"], 1740.0, places=1)

    def test_skips_null_weight_sets(self):
        make_workout(self.user, datetime(2026, 2, 1, tzinfo=dt_timezone.utc),
                     self.exercise, [(None, 5), (Decimal("100"), 5)])
        res = self._get()
        self.assertAlmostEqual(res.data["points"][0]["value"], 500.0, places=1)

    def test_summary_multiple_days(self):
        make_workout(self.user, datetime(2026, 2, 1, tzinfo=dt_timezone.utc),
                     self.exercise, [(Decimal("100"), 5)])   # 500
        make_workout(self.user, datetime(2026, 3, 1, tzinfo=dt_timezone.utc),
                     self.exercise, [(Decimal("100"), 10)])  # 1000
        res = self._get()
        self.assertEqual(res.data["summary"]["start"], 500.0)
        self.assertEqual(res.data["summary"]["latest"], 1000.0)
        self.assertEqual(res.data["summary"]["change"], 500.0)

    def test_empty_returns_null_summary(self):
        res = self._get()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIsNone(res.data["summary"]["start"])


# ---------------------------------------------------------------------------
# Weekly volume
# ---------------------------------------------------------------------------

class WeeklyVolumeTests(APITestCase):
    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.exercise = create_exercise()

    def _get(self, extra=None):
        params = {"exercise_id": self.exercise.id}
        if extra:
            params.update(extra)
        return self.client.get(WEEKLY_VOLUME_URL, params)

    def test_returns_200(self):
        res = self._get()
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_default_12_weeks_of_points(self):
        res = self._get()
        self.assertEqual(len(res.data["points"]), 12)

    def test_custom_weeks_param(self):
        res = self._get({"weeks": 4})
        self.assertEqual(len(res.data["points"]), 4)

    def test_exercise_id_required(self):
        res = self.client.get(WEEKLY_VOLUME_URL)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_volume_accumulates_into_correct_week(self):
        # Use a fixed Monday so we know the bucket key
        monday = date.today() - timedelta(days=date.today().weekday())  # this week's Monday
        performed_at = datetime(monday.year, monday.month, monday.day, 12, 0, tzinfo=dt_timezone.utc)
        make_workout(self.user, performed_at, self.exercise, [(Decimal("100"), 5)])  # 500

        res = self._get({"weeks": 1, "to": monday.strftime("%Y-%m-%d")})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        week_key = monday.strftime("%Y-%m-%d")
        week_point = next((p for p in res.data["points"] if p["week_start"] == week_key), None)
        self.assertIsNotNone(week_point)
        self.assertAlmostEqual(week_point["value"], 500.0, places=1)

    def test_other_user_data_excluded(self):
        other_user = create_user(username="other2@example.com", email="other2@example.com")
        monday = date.today() - timedelta(days=date.today().weekday())
        performed_at = datetime(monday.year, monday.month, monday.day, 12, 0, tzinfo=dt_timezone.utc)
        make_workout(other_user, performed_at, self.exercise, [(Decimal("100"), 5)])

        res = self._get({"weeks": 1, "to": monday.strftime("%Y-%m-%d")})
        for point in res.data["points"]:
            self.assertEqual(point["value"], 0.0)


# ---------------------------------------------------------------------------
# Export sets
# ---------------------------------------------------------------------------

class ExportSetsTests(APITestCase):
    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.exercise = create_exercise()

    def _get(self, extra=None):
        params = {}
        if extra:
            params.update(extra)
        return self.client.get(EXPORT_SETS_URL, params)

    def test_returns_200(self):
        res = self._get()
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_returns_all_sets_for_user(self):
        make_workout(self.user, datetime(2026, 2, 1, tzinfo=dt_timezone.utc),
                     self.exercise, [(Decimal("100"), 5), (Decimal("90"), 8)])
        res = self._get()
        self.assertEqual(res.data["count"], 2)

    def test_row_shape(self):
        make_workout(self.user, datetime(2026, 2, 1, tzinfo=dt_timezone.utc),
                     self.exercise, [(Decimal("100"), 5)])
        res = self._get()
        row = res.data["results"][0]
        for key in ("workout_id", "performed_at", "exercise_id", "exercise_name",
                    "workout_exercise_id", "order", "set_id", "set_number", "reps", "weight"):
            self.assertIn(key, row)

    def test_null_weight_serialized_as_none(self):
        make_workout(self.user, datetime(2026, 2, 1, tzinfo=dt_timezone.utc),
                     self.exercise, [(None, 5)])
        res = self._get()
        self.assertIsNone(res.data["results"][0]["weight"])

    def test_exercise_id_filter(self):
        other_exercise = create_exercise(name="other exercise")
        make_workout(self.user, datetime(2026, 2, 1, tzinfo=dt_timezone.utc),
                     self.exercise, [(Decimal("100"), 5)])
        make_workout(self.user, datetime(2026, 2, 2, tzinfo=dt_timezone.utc),
                     other_exercise, [(Decimal("200"), 5)])
        res = self._get({"exercise_id": self.exercise.id})
        self.assertEqual(res.data["count"], 1)
        self.assertEqual(res.data["results"][0]["exercise_id"], self.exercise.id)

    def test_date_range_filter(self):
        make_workout(self.user, datetime(2026, 1, 1, tzinfo=dt_timezone.utc),
                     self.exercise, [(Decimal("100"), 5)])
        make_workout(self.user, datetime(2026, 6, 1, tzinfo=dt_timezone.utc),
                     self.exercise, [(Decimal("110"), 5)])
        res = self._get({"performed_from": "2026-06-01", "performed_to": "2026-12-31"})
        self.assertEqual(res.data["count"], 1)

    def test_other_user_data_excluded(self):
        other_user = create_user(username="other3@example.com", email="other3@example.com")
        make_workout(other_user, datetime(2026, 2, 1, tzinfo=dt_timezone.utc),
                     self.exercise, [(Decimal("200"), 5)])
        res = self._get()
        self.assertEqual(res.data["count"], 0)

    def test_pagination_structure(self):
        res = self._get()
        self.assertIn("count", res.data)
        self.assertIn("results", res.data)

    def test_performed_from_after_performed_to_returns_400(self):
        res = self._get({"performed_from": "2026-12-31", "performed_to": "2026-01-01"})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
