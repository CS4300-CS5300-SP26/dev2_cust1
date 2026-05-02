"""Step definitions for training / workout BDD scenarios."""

import json
from datetime import date

from behave import given, when, then
from django.contrib.auth.models import User

from core.models import Workout, Exercise


def _get_train_user(context):
    return User.objects.get(username='trainuser@spotter.ai')


# ── Given ──────────────────────────────────────────────────────────────────────

@given('a workout named "{name}" exists for today')
def step_workout_exists_today(context, name):
    user = _get_train_user(context)
    context.current_workout = Workout.objects.create(
        user=user, name=name, goal='strength', status='planned', date=date.today()
    )


@given('a planned workout named "{name}" exists for today')
def step_planned_workout_named_today(context, name):
    user = _get_train_user(context)
    context.current_workout = Workout.objects.create(
        user=user, name=name, goal='strength', status='planned', date=date.today()
    )


@given('an exercise "{name}" in muscle group "{group}" exists in that workout')
def step_exercise_exists_in_workout(context, name, group):
    context.current_exercise = Exercise.objects.create(
        workout=context.current_workout,
        name=name,
        muscle_group=group,
        sets=3,
        reps=10,
        completed=False,
    )


@given('a completed exercise "{name}" in muscle group "{group}" exists in that workout')
def step_completed_exercise_exists(context, name, group):
    context.current_exercise = Exercise.objects.create(
        workout=context.current_workout,
        name=name,
        muscle_group=group,
        sets=3,
        reps=10,
        completed=True,
    )


@given('another training user has a workout')
def step_other_training_user_workout(context):
    other = User.objects.filter(username='other_trainuser@spotter.ai').first()
    if not other:
        other = User.objects.create_user(
            username='other_trainuser@spotter.ai',
            email='other_trainuser@spotter.ai',
            password='testpass123',
        )
    context.other_workout = Workout.objects.create(
        user=other, name='Other Workout', goal='strength', status='planned', date=date.today()
    )


# ── When ──────────────────────────────────────────────────────────────────────

@when('I add a workout named "{name}" with goal "{goal}" and status "{status}" for today')
def step_add_workout(context, name, goal, status):
    context.response = context.test.client.post('/train/add_workout/', {
        'workout_name': name,
        'goal': goal,
        'status': status,
        'date': date.today().strftime('%Y-%m-%d'),
    })


@when('I try to add a workout with no name for today')
def step_add_workout_no_name(context):
    context.response = context.test.client.post('/train/add_workout/', {
        'workout_name': '',
        'goal': 'strength',
        'status': 'planned',
        'date': date.today().strftime('%Y-%m-%d'),
    })


@when('I delete that workout')
def step_delete_workout(context):
    context.response = context.test.client.post('/train/delete_workout/', {
        'workout_id': context.current_workout.id,
        'date': date.today().strftime('%Y-%m-%d'),
    })


@when('I add an exercise "{name}" in muscle group "{group}" to that workout')
def step_add_exercise(context, name, group):
    context.response = context.test.client.post('/train/add_exercise/', {
        'workout_id': context.current_workout.id,
        'exercise_name': name,
        'muscle_group': group,
        'date': date.today().strftime('%Y-%m-%d'),
    })


@when('I try to add an exercise with no name to that workout')
def step_add_exercise_no_name(context):
    context.response = context.test.client.post('/train/add_exercise/', {
        'workout_id': context.current_workout.id,
        'exercise_name': '',
        'muscle_group': 'chest',
        'date': date.today().strftime('%Y-%m-%d'),
    })


@when('I toggle that exercise')
def step_toggle_exercise(context):
    context.response = context.test.client.post('/train/toggle_exercise/', {
        'exercise_id': context.current_exercise.id,
        'date': date.today().strftime('%Y-%m-%d'),
    })


@when('I delete that exercise')
def step_delete_exercise(context):
    context.response = context.test.client.post('/train/delete_exercise/', {
        'exercise_id': context.current_exercise.id,
        'date': date.today().strftime('%Y-%m-%d'),
    })


@when('I edit that exercise to name "{name}" in muscle group "{group}"')
def step_edit_exercise(context, name, group):
    context.response = context.test.client.post('/train/edit_exercise/', {
        'exercise_id': context.current_exercise.id,
        'exercise_name': name,
        'muscle_group': group,
        'status': 'planned',
        'date': date.today().strftime('%Y-%m-%d'),
    })


@when('I complete that workout via the complete_workout API')
def step_complete_workout_api(context):
    context.response = context.test.client.post(
        '/api/workout/complete/',
        data=json.dumps({'workout_id': context.current_workout.id}),
        content_type='application/json',
    )


@when('I POST to "{url}" with JSON "{payload}"')
def step_post_json(context, url, payload):
    context.response = context.test.client.post(
        url,
        data=payload,
        content_type='application/json',
    )


@when('I try to complete the other user\'s workout via the API')
def step_complete_other_workout_api(context):
    context.response = context.test.client.post(
        '/api/workout/complete/',
        data=json.dumps({'workout_id': context.other_workout.id}),
        content_type='application/json',
    )


@when('I save workout time of {seconds:d} seconds via the API')
def step_save_workout_time(context, seconds):
    context.response = context.test.client.post(
        '/api/workout/save_time/',
        data=json.dumps({'workout_id': context.current_workout.id, 'total_seconds': seconds}),
        content_type='application/json',
    )


@when('I complete all exercises in that workout via the API')
def step_complete_exercises_by_ids(context):
    exercise_ids = list(
        Exercise.objects.filter(workout=context.current_workout).values_list('id', flat=True)
    )
    context.response = context.test.client.post(
        '/api/exercises/complete_by_ids/',
        data=json.dumps({'exercise_ids': exercise_ids}),
        content_type='application/json',
    )


@when('I save set progress for that exercise')
def step_save_set_progress(context):
    context.response = context.test.client.post(
        '/api/set_progress/save/',
        data=json.dumps({
            'workout_id': context.current_workout.id,
            'set_data': [
                {'exercise_id': context.current_exercise.id, 'set_number': 1, 'completed': True}
            ],
            'timer_seconds': 0,
        }),
        content_type='application/json',
    )


@when('I get set progress for that workout')
def step_get_set_progress(context):
    context.response = context.test.client.get(
        f'/api/set_progress/get/?workout_id={context.current_workout.id}'
    )


@when('I GET "{url}" without workout_id')
def step_get_without_workout_id(context, url):
    context.response = context.test.client.get(url)


@when('I try to delete the other user\'s workout')
def step_delete_other_workout(context):
    context.response = context.test.client.post('/train/delete_workout/', {
        'workout_id': context.other_workout.id,
        'date': date.today().strftime('%Y-%m-%d'),
    })


# ── Then ──────────────────────────────────────────────────────────────────────

@then('a workout named "{name}" should exist for today')
def step_workout_exists_check(context, name):
    user = _get_train_user(context)
    assert Workout.objects.filter(user=user, name=name, date=date.today()).exists(), (
        f'Workout "{name}" not found for today'
    )


@then('no new workout should exist')
def step_no_workout_exists(context):
    user = _get_train_user(context)
    assert not Workout.objects.filter(user=user, name='').exists()


@then('no workout named "{name}" should exist')
def step_workout_not_exists(context, name):
    user = _get_train_user(context)
    assert not Workout.objects.filter(user=user, name=name).exists(), (
        f'Workout "{name}" should have been deleted but still exists'
    )


@then('an exercise named "{name}" should exist in the workout')
def step_exercise_exists_check(context, name):
    assert Exercise.objects.filter(workout=context.current_workout, name=name).exists(), (
        f'Exercise "{name}" not found in workout'
    )


@then('no exercise should exist in the workout')
def step_no_exercise_exists(context):
    assert not Exercise.objects.filter(workout=context.current_workout).exists()


@then('the exercise should be marked as completed')
def step_exercise_completed(context):
    context.current_exercise.refresh_from_db()
    assert context.current_exercise.completed, 'Exercise should be completed but is not'


@then('the exercise should be marked as incomplete')
def step_exercise_incomplete(context):
    context.current_exercise.refresh_from_db()
    assert not context.current_exercise.completed, 'Exercise should be incomplete but is completed'


@then('the exercise should no longer exist')
def step_exercise_deleted(context):
    assert not Exercise.objects.filter(id=context.current_exercise.id).exists(), (
        'Exercise should have been deleted but still exists'
    )


@then('the other user\'s workout should still exist')
def step_other_workout_still_exists(context):
    assert Workout.objects.filter(id=context.other_workout.id).exists(), (
        "Other user's workout was deleted — authorization failed"
    )
