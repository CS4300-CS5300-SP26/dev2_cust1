"""Step definitions for achievements and challenges BDD scenarios."""

import json
from datetime import date, timedelta

from behave import given, when, then
from django.contrib.auth.models import User

from core.models import Meal, FoodItem, Workout, Exercise


def _get_ach_user(context):
    return User.objects.get(username='achuser@spotter.ai')


# ── Given: workout helpers ───────────────────────────────────────────────────

@given('a completed workout exists for today with a completed exercise')
def step_completed_workout_with_exercise(context):
    user = _get_ach_user(context)
    workout = Workout.objects.create(
        user=user, name='Test Workout', goal='strength',
        status='completed', date=date.today()
    )
    Exercise.objects.create(
        workout=workout, name='Push-up', sets=3, reps=10, completed=True
    )
    context.current_workout = workout


@given('a completed workout exists for today with no exercises')
def step_completed_workout_no_exercises(context):
    user = _get_ach_user(context)
    context.current_workout = Workout.objects.create(
        user=user, name='Empty Workout', goal='strength',
        status='completed', date=date.today()
    )


@given('a planned workout exists for today')
def step_planned_workout_today(context):
    user = _get_ach_user(context)
    context.current_workout = Workout.objects.create(
        user=user, name='Planned Workout', goal='strength',
        status='planned', date=date.today()
    )


@given('I completed a workout today')
def step_completed_workout_today(context):
    user = _get_ach_user(context)
    context.current_workout = Workout.objects.create(
        user=user, name='Today Workout', goal='strength',
        status='completed', date=date.today()
    )


@given('I completed a workout {days:d} days ago')
def step_completed_workout_days_ago(context, days):
    user = _get_ach_user(context)
    d = date.today() - timedelta(days=days)
    context.current_workout = Workout.objects.create(
        user=user, name='Old Workout', goal='strength',
        status='completed', date=d
    )


@given('I have completed {count:d} workouts this week')
def step_completed_workouts_this_week(context, count):
    user = _get_ach_user(context)
    for i in range(count):
        Workout.objects.create(
            user=user, name=f'Workout {i}', goal='strength',
            status='completed', date=date.today() - timedelta(days=i)
        )


@given('I have not completed any workouts this week')
def step_no_workouts_this_week(context):
    pass  # Default state for a fresh user


# ── Given: meal helpers ───────────────────────────────────────────────────────

@given('I have logged meals on {count:d} different days')
def step_meals_on_days(context, count):
    user = _get_ach_user(context)
    for i in range(count):
        d = date.today() - timedelta(days=i)
        meal = Meal.objects.create(user=user, name=f'Meal day {i}', date=d)
        FoodItem.objects.create(
            meal=meal, name='Food', calories=500,
            protein=20, carbs=50, fats=10
        )


@given('I have logged a meal today')
def step_logged_meal_today(context):
    user = _get_ach_user(context)
    meal = Meal.objects.create(user=user, name='Today Meal', date=date.today())
    FoodItem.objects.create(
        meal=meal, name='Food', calories=500, protein=20, carbs=50, fats=10
    )
    context.current_meal = meal


@given('I have not logged any meals today')
def step_no_meals_today(context):
    pass  # Default state for a fresh user


# ── Given: other user helpers ─────────────────────────────────────────────────

@given('another user has completed {count:d} exercises')
def step_other_user_exercises(context, count):
    other, _ = User.objects.get_or_create(
        username='otheriron@spotter.ai',
        defaults={'email': 'otheriron@spotter.ai', 'is_active': True}
    )
    other.set_password('testpass123')
    other.save()
    workout = Workout.objects.create(
        user=other, name='Other Workout', goal='strength',
        status='completed', date=date.today()
    )
    for _ in range(count):
        Exercise.objects.create(
            workout=workout, name='E', sets=3, reps=10, completed=True
        )


# ── When: API interaction ─────────────────────────────────────────────────────

@when('I complete that workout via the API')
def step_complete_workout_api(context):
    context.response = context.test.client.post(
        '/api/workout/complete/',
        data=json.dumps({'workout_id': context.current_workout.id}),
        content_type='application/json'
    )


# ── Then: JSON assertions ─────────────────────────────────────────────────────

@then('the response is valid JSON')
def step_response_is_json(context):
    try:
        context.response_json = json.loads(context.response.content)
    except json.JSONDecodeError as e:
        raise AssertionError(f'Response is not valid JSON: {e}')


@then('the JSON has key "{key}"')
def step_json_has_key(context, key):
    if not hasattr(context, 'response_json'):
        context.response_json = json.loads(context.response.content)
    assert key in context.response_json, (
        f'Key "{key}" not found. Keys: {list(context.response_json.keys())}'
    )


@then('the JSON "{key}" list is empty')
def step_json_list_empty(context, key):
    if not hasattr(context, 'response_json'):
        context.response_json = json.loads(context.response.content)
    assert context.response_json[key] == [], (
        f'Expected "{key}" to be empty, got: {context.response_json[key]}'
    )


@then('the JSON stats "{key}" is {value:d}')
def step_json_stats_value(context, key, value):
    if not hasattr(context, 'response_json'):
        context.response_json = json.loads(context.response.content)
    actual = context.response_json['stats'][key]
    assert actual == value, f'Expected stats["{key}"] == {value}, got {actual}'


# ── Then: achievement assertions ──────────────────────────────────────────────

@then('"{ach_id}" is in the earned achievement IDs')
def step_ach_in_earned(context, ach_id):
    if not hasattr(context, 'response_json'):
        context.response_json = json.loads(context.response.content)
    earned = context.response_json['earned_ids']
    assert ach_id in earned, f'"{ach_id}" not in earned_ids: {earned}'


@then('"{ach_id}" is not in the earned achievement IDs')
def step_ach_not_in_earned(context, ach_id):
    if not hasattr(context, 'response_json'):
        context.response_json = json.loads(context.response.content)
    earned = context.response_json['earned_ids']
    assert ach_id not in earned, f'"{ach_id}" should not be in earned_ids: {earned}'


# ── Then: challenge assertions ────────────────────────────────────────────────

def _get_challenge(response_json, challenge_id):
    challenges = response_json['challenges']
    for c in challenges:
        if c['id'] == challenge_id:
            return c
    raise AssertionError(
        f'Challenge "{challenge_id}" not found. Available: {[c["id"] for c in challenges]}'
    )


@then('the challenge "{ch_id}" has progress {value:d}')
def step_challenge_progress(context, ch_id, value):
    if not hasattr(context, 'response_json'):
        context.response_json = json.loads(context.response.content)
    ch = _get_challenge(context.response_json, ch_id)
    assert ch['progress'] == value, (
        f'Challenge "{ch_id}" progress: expected {value}, got {ch["progress"]}'
    )


@then('the challenge "{ch_id}" is completed')
def step_challenge_completed(context, ch_id):
    if not hasattr(context, 'response_json'):
        context.response_json = json.loads(context.response.content)
    ch = _get_challenge(context.response_json, ch_id)
    assert ch['completed'], f'Challenge "{ch_id}" should be completed but is not'


# ── Then: complete_workout achievement progress ────────────────────────────────

@then('the achievement progress has "{key}"')
def step_ach_progress_has_key(context, key):
    if not hasattr(context, 'response_json'):
        context.response_json = json.loads(context.response.content)
    ach_progress = context.response_json['achievement_progress']
    assert key in ach_progress, (
        f'"{key}" not in achievement_progress. Keys: {list(ach_progress.keys())}'
    )


@then('the workout_3x challenge progress is at least 1 in the response')
def step_workout_3x_at_least_1(context):
    if not hasattr(context, 'response_json'):
        context.response_json = json.loads(context.response.content)
    challenges = context.response_json['achievement_progress']['challenges']
    ch = next((c for c in challenges if c['id'] == 'workout_3x'), None)
    assert ch is not None, 'workout_3x challenge not found in achievement_progress'
    assert ch['progress'] >= 1, (
        f'workout_3x progress should be >= 1, got {ch["progress"]}'
    )
