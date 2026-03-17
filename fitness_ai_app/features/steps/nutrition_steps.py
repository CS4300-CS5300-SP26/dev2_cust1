"""Step definitions for nutrition-tracking BDD scenarios."""

from datetime import date

from behave import given, when, then
from django.contrib.auth.models import User

from core.models import Meal, FoodItem


# ── Given steps ──────────────────────────────────────────────────────────────

@given('a meal named "{name}" exists for today')
def step_meal_exists_today(context, name):
    user = User.objects.get(username='nutrition@spotter.ai')
    context.current_meal = Meal.objects.create(
        user=user, name=name, date=date.today()
    )


@given('a food item "{name}" with {calories:d} calories exists in that meal')
def step_food_item_exists(context, name, calories):
    context.current_food_item = FoodItem.objects.create(
        meal=context.current_meal, name=name, calories=calories
    )


@given('a completed food item "{name}" with {calories:d} calories exists in that meal')
def step_completed_food_item_exists(context, name, calories):
    context.current_food_item = FoodItem.objects.create(
        meal=context.current_meal, name=name, calories=calories, completed=True
    )


@given('another user has a meal named "{name}"')
def step_other_user_meal(context, name):
    other_user, _ = User.objects.get_or_create(
        username='other@spotter.ai',
        defaults={'email': 'other@spotter.ai', 'is_active': True},
    )
    other_user.set_password('otherpass123')
    other_user.save()
    context.other_meal = Meal.objects.create(
        user=other_user, name=name, date=date.today()
    )


# ── When steps ───────────────────────────────────────────────────────────────

@when('I add a meal named "{name}" for date "{date_str}"')
def step_add_meal(context, name, date_str):
    context.response = context.test.client.post('/nutrition/add_meal/', {
        'meal_name': name,
        'date': date_str,
    })


@when('I try to add a meal with name "{name}" for date "{date_str}"')
def step_try_add_meal(context, name, date_str):
    context.response = context.test.client.post('/nutrition/add_meal/', {
        'meal_name': name,
        'date': date_str,
    })


@when('I try to add a meal with no name for date "{date_str}"')
def step_try_add_meal_no_name(context, date_str):
    context.response = context.test.client.post('/nutrition/add_meal/', {
        'meal_name': '',
        'date': date_str,
    })


@when('I add a food item "{name}" with {calories:d} calories to that meal')
def step_add_food_item(context, name, calories):
    context.response = context.test.client.post('/nutrition/add_food_item/', {
        'meal_id': context.current_meal.id,
        'food_name': name,
        'food_calories': str(calories),
        'date': str(date.today()),
    })


@when('I try to add a food item "{name}" with "{calories}" calories to that meal')
def step_try_add_food_item_invalid(context, name, calories):
    context.response = context.test.client.post('/nutrition/add_food_item/', {
        'meal_id': context.current_meal.id,
        'food_name': name,
        'food_calories': calories,
        'date': str(date.today()),
    })


@when('I toggle the food item')
def step_toggle_food_item(context):
    context.response = context.test.client.post('/nutrition/toggle_food_item/', {
        'item_id': context.current_food_item.id,
        'date': str(date.today()),
    })


@when('I delete the food item')
def step_delete_food_item(context):
    context.response = context.test.client.post('/nutrition/delete_food_item/', {
        'item_id': context.current_food_item.id,
        'date': str(date.today()),
    })


@when('I try to add a food item to the other user\'s meal')
def step_add_to_other_meal(context):
    context.response = context.test.client.post('/nutrition/add_food_item/', {
        'meal_id': context.other_meal.id,
        'food_name': 'Hack Food',
        'food_calories': '100',
        'date': str(date.today()),
    })


# ── Then steps ───────────────────────────────────────────────────────────────

@then('the response status code should be {code:d}')
def step_status_code(context, code):
    assert context.response.status_code == code, (
        f'Expected {code}, got {context.response.status_code}'
    )


@then('a meal named "{name}" should exist for date "{date_str}"')
def step_meal_exists(context, name, date_str):
    user = User.objects.get(username='nutrition@spotter.ai')
    assert Meal.objects.filter(user=user, name=name, date=date_str).exists(), (
        f'Meal "{name}" for {date_str} not found'
    )


@then('no meals should exist')
def step_no_meals(context):
    user = User.objects.get(username='nutrition@spotter.ai')
    assert Meal.objects.filter(user=user).count() == 0, 'Expected no meals'


@then('a food item named "{name}" with {calories:d} calories should exist')
def step_food_item_exists_check(context, name, calories):
    assert FoodItem.objects.filter(name=name, calories=calories).exists(), (
        f'FoodItem "{name}" ({calories} kcal) not found'
    )


@then('no food items should exist')
def step_no_food_items(context):
    assert FoodItem.objects.count() == 0, 'Expected no food items'


@then('the food item should be marked as completed')
def step_food_item_completed(context):
    context.current_food_item.refresh_from_db()
    assert context.current_food_item.completed is True, 'Food item not completed'


@then('the food item should be marked as incomplete')
def step_food_item_incomplete(context):
    context.current_food_item.refresh_from_db()
    assert context.current_food_item.completed is False, 'Food item still completed'


@then('the food item should no longer exist')
def step_food_item_deleted(context):
    assert not FoodItem.objects.filter(id=context.current_food_item.id).exists(), (
        'Food item still exists'
    )


@then('the total calories should be {expected:d}')
def step_total_calories(context, expected):
    actual = context.response.context['total_calories']
    assert actual == expected, f'Expected {expected} calories, got {actual}'
