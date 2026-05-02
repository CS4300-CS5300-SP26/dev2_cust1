"""Step definitions for home dashboard BDD scenarios."""

from datetime import date

from behave import given
from django.contrib.auth.models import User

from core.models import Meal, FoodItem, Workout, Exercise


def _get_dash_user(context):
    return User.objects.get(username='dashuser@spotter.ai')


# ── Given ──────────────────────────────────────────────────────────────────────

@given('a dash meal exists for today with a completed food item of {calories:d} calories')
def step_dash_meal_completed_item(context, calories):
    user = _get_dash_user(context)
    meal = Meal.objects.create(user=user, name='Dash Meal', date=date.today())
    FoodItem.objects.create(
        meal=meal, name='Completed Food', calories=calories,
        protein=20, carbs=50, fats=10, completed=True
    )


@given('a dash meal exists for today with an incomplete food item of {calories:d} calories')
def step_dash_meal_incomplete_item(context, calories):
    user = _get_dash_user(context)
    meal = Meal.objects.create(user=user, name='Dash Meal', date=date.today())
    FoodItem.objects.create(
        meal=meal, name='Incomplete Food', calories=calories,
        protein=20, carbs=50, fats=10, completed=False
    )


@given('a dash workout exists for today with {count:d} completed exercises')
def step_dash_workout_with_exercises(context, count):
    user = _get_dash_user(context)
    workout = Workout.objects.create(
        user=user, name='Dash Workout', goal='strength', status='planned', date=date.today()
    )
    for i in range(count):
        Exercise.objects.create(
            workout=workout, name=f'Exercise {i}', muscle_group='chest',
            sets=3, reps=10, completed=True
        )
