from datetime import datetime, date, time, timedelta
from decimal import Decimal
from django.urls import reverse

def get_monday(incoming_date: date) -> list[date]:
    return incoming_date - timedelta(days=incoming_date.weekday())

def week_buckets( start: date, end: date, duration: int = None):
    weeks = []

    if (duration == None) or (start and end and duration):
        starting_week = get_monday(start)
        end_week = get_monday(end)
        current_week = starting_week
        while current_week <= end_week:
            weeks.append({
                'date': current_week.strftime('%Y-%m-%d'),
                'value': 0
            })
            current_week += timedelta(days=7)
    elif (start and duration):
        mon_of_duration_week = start - timedelta(start.weekday())
        counter = 0
        while (counter < duration):
            weeks.append({
                'week_start': mon_of_duration_week.strftime('%Y-%m-%d'),
                'value': 0
            })
            mon_of_duration_week += timedelta(days=7)
            counter += 1
    elif (end and duration):
        mon_of_duration_week = end - timedelta(end.weekday())
        counter = 0
        while (counter < duration):
            weeks.append({
                'week_start': mon_of_duration_week.strftime('%Y-%m-%d'),
                'value': 0
            })
            mon_of_duration_week -= timedelta(days=7)
            counter += 1

    return weeks

def calculate_weekly_top_set(user_workouts, performed_from:datetime, performed_to:datetime, exercise_id:int):
    wk_buckets = week_buckets(performed_from, performed_to)
    week_bucket = { week['date']:week for week in wk_buckets }
    for user_workout in user_workouts:
        weight_from_best_set = 0
        for we in user_workout.workout_exercises.all():
            for ws in we.workout_sets.all():
                weight_from_best_set = ws.weight if ws.weight > weight_from_best_set else weight_from_best_set

        week_of_workout = (user_workout.performed_at - timedelta(days=user_workout.performed_at.weekday())).strftime('%Y-%m-%d')
        week_bucket[week_of_workout]['value'] = max(week_bucket[week_of_workout]['value'], weight_from_best_set)
    starting_weight = list(week_bucket.values())[0]['value']
    latest_weight = list(week_bucket.values())[-1]['value']
    change_in_weight = abs(latest_weight - starting_weight)
    if not wk_buckets:
        summary = {
            'start':None,
            'latest':None,
            'change':None
        }
    else:
        summary = {
            'start':starting_weight,
            'latest':latest_weight,
            'change': change_in_weight
        }
    return {
        'exercise_id': exercise_id,
        'metric': 'top_set_weight',
        'unit': 'lbs_reps',
        'points': wk_buckets,
        'summary': summary
    }

def calculate_daily_1_rep_max(user_workouts, performed_from:datetime, performed_to:datetime, exercise_id:int):
    points = []
    for user_workout in user_workouts:
        daily_1_rep_max = 0
        weight_from_best_set = 0
        reps_from_best_set = 0
        weight_reps_from_best_set = ()
        for we in user_workout.workout_exercises.all():
            for ws in we.workout_sets.all():
                weight_reps_from_best_set = (ws.weight, ws.reps) if ws.weight > weight_from_best_set else (weight_from_best_set,reps_from_best_set)
        daily_1_rep_max = round(weight_reps_from_best_set[0] * (1 + (weight_reps_from_best_set[1] / Decimal(30))),2)
        points.append({
            'date':user_workout.performed_at.strftime('%Y-%m-%d'),
            'value':daily_1_rep_max
        })
    starting_1_rep_max = points[0]['value']
    latest_1_rep_max = points[-1]['value']
    change_in_1_rep_max = abs(latest_1_rep_max - starting_1_rep_max)
    summary = {
        'start':starting_1_rep_max,
        'latest':latest_1_rep_max,
        'change': change_in_1_rep_max
    }
    
    return {
        'exercise_id': exercise_id,
        'metric': 'estimated_1rm',
        'unit': 'lbs_reps',
        'points': points,
        'summary': summary
    }

def calculate_daily_tonnage(user_workouts, performed_from:datetime, performed_to:datetime, exercise_id:int):
    points = []
    for user_workout in user_workouts:
        overall_volume = 0
        for we in user_workout.workout_exercises.all():
            for ws in we.workout_sets.all():
                overall_volume += ws.weight * ws.reps
        overall_volume = round(overall_volume,2)
        points.append({
            'date':user_workout.performed_at.strftime('%Y-%m-%d'),
            'value':overall_volume
        })
    starting_volume = points[0]['value']
    latest_volume = points[-1]['value']
    change_in_volume = abs(latest_volume - starting_volume)
    summary = {
        'start':starting_volume,
        'latest':latest_volume,
        'change': change_in_volume
    }
    
    return {
        'exercise_id': exercise_id,
        'metric': 'tonnage',
        'unit': 'lbs_reps',
        'points': points,
        'summary': summary
    }

def calculate_weekly_volume(user_workouts, duration:int, to:datetime, exercise_id:int):
    wk_buckets = week_buckets(None, to, duration)
    points = { week['week_start']:week for week in wk_buckets}
    print(points)
    for user_workout in user_workouts:
        weekly_tonnage = 0
        for we in user_workout.workout_exercises.all():
            for ws in we.workout_sets.all():
                weekly_tonnage += ws.weight * ws.reps
        week_of_workout = (user_workout.performed_at - timedelta(days=user_workout.performed_at.weekday())).strftime('%Y-%m-%d')
        points[week_of_workout]['value'] += weekly_tonnage
    
    return {
        'exercise_id': exercise_id,
        'unit': 'lbs_reps',
        'weeks': duration,
        'points': points,
    }

def calculate_export_sets(user_workouts, performed_from:datetime, performed_to:datetime, exercise_id:int, page:int = 1, page_size:int = 200):
    results = []
    if (page and page > 1):
        next_url = reverse("insights:export-sets") + f"?page={page}&page_size={page_size}"
        previous_url = reverse("insights:export-sets") + f"?page={page-1}&page_size={page_size}"
    else:
        next_url = reverse("insights:export-sets") + f"?page=1&page_size={page_size}"
        previous_url = None

    
    for user_workout in user_workouts:
        for we in user_workout.workout_exercises.all():
            for ws in we.workout_sets.all():
                results.append({
                    'workout_id': we.workout.id,
                    'performed_at': user_workout.performed_at.strftime('%Y-%m-%d'),
                    'exercise_id': we.exercise.id,
                    'exercise_name': we.exercise.name,
                    'workout_exercise_id': we.id,
                    'order': we.order,
                    'set_id': ws.id,
                    'set_number': ws.set_number,
                    'reps': ws.reps,
                    'weight': ws.weight,
                })
    return {
        'next': next_url,
        'previous': previous_url,
        'count': len(results),
        'results': results,
    }