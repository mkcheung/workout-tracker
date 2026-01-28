from datetime import datetime, date, time, timedelta

def get_monday(incoming_date: date) -> list[date]:
    return incoming_date - timedelta(days=incoming_date.weekday())

def week_buckets( start: date, end: date):
    starting_week = get_monday(start)
    end_week = get_monday(end)
    weeks = []
    current_week = starting_week
    while current_week <= end_week:
        weeks.append({
            'date': current_week.strftime('%Y-%m-%d'),
            'value': 0
        })
        current_week += timedelta(days=7)
    return weeks

def calculate_weekly_volume(user_workouts, performed_from:datetime, performed_to:datetime, exercise_id:int):
    wk_buckets = week_buckets(performed_from, performed_to)
    for user_workout in user_workouts:
        weight_from_best_set = 0
        for we in user_workout.workout_exercises.all():
            for ws in we.workout_sets.all():
                weight_from_best_set = ws.weight if ws.weight > weight_from_best_set else weight_from_best_set

        week_of_workout = (user_workout.performed_at - timedelta(days=user_workout.performed_at.weekday())).strftime('%Y-%m-%d')
        week_bucket = [ week for week in wk_buckets if week['date'] == week_of_workout ]
        week_bucket[0]['value'] = weight_from_best_set

    return {
        "exercise_id": exercise_id,
        'unit': 'lbs_reps',
        'weeks': len(wk_buckets),
        'points': wk_buckets
    }

    