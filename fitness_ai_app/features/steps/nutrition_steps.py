"""Step definitions for nutrition-tracking BDD scenarios."""

import json
from datetime import date

from behave import given, when, then
from django.contrib.auth.models import User

from datetime import date as date_cls

from core.models import Meal, FoodItem, SavedFood, SavedMeal


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


@given('the system food database contains "{food_name}"')
def step_system_food_exists(context, food_name):
    system_user, _ = User.objects.get_or_create(
        username='system@spotter.ai',
        defaults={'email': 'system@spotter.ai', 'is_active': False}
    )
    system_meal, _ = Meal.objects.get_or_create(
        user=system_user, name='Food Database', date=date_cls(2000, 1, 1)
    )
    FoodItem.objects.get_or_create(
        meal=system_meal, name=food_name,
        defaults={'calories': 150, 'protein': 10, 'carbs': 15, 'fats': 5}
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


@when('I add a food item "{name}" with {calories:d} calories and {servings:d} servings of "{unit}" to that meal')
def step_add_food_item_with_servings(context, name, calories, servings, unit):
    context.response = context.test.client.post('/nutrition/add_food_item/', {
        'meal_id': context.current_meal.id,
        'food_name': name,
        'food_calories': str(calories),
        'serving_size': str(servings),
        'serving_unit': unit,
        'date': str(date.today()),
    })
    context.last_food_name = name


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


@when('I edit the food item with {servings:d} servings and {calories:d} calories')
def step_edit_food_item(context, servings, calories):
    item = context.current_food_item
    context.response = context.test.client.post('/nutrition/add_food_item/', {
        'meal_id': context.current_meal.id,
        'item_id': item.id,
        'food_name': item.name,
        'food_calories': str(calories),
        'protein': str(item.protein),
        'carbs': str(item.carbs),
        'fats': str(item.fats),
        'serving_size': str(servings),
        'serving_unit': item.serving_unit,
        'date': str(date.today()),
    })


@when('I search foods for "{query}"')
def step_search_foods(context, query):
    context.response = context.test.client.get(f'/api/search_foods/?q={query}')


@when('I fetch all foods')
def step_fetch_all_foods(context):
    context.response = context.test.client.get('/api/all_foods/')


@when('I try to add a food item to the other user\'s meal')
def step_add_to_other_meal(context):
    context.response = context.test.client.post('/nutrition/add_food_item/', {
        'meal_id': context.other_meal.id,
        'food_name': 'Hack Food',
        'food_calories': '100',
        'date': str(date.today()),
    })


# ── Then steps ───────────────────────────────────────────────────────────────

@then('the search results should include "{food_name}"')
def step_search_results_include(context, food_name):
    data = json.loads(context.response.content)
    names = [r['name'] for r in data.get('results', [])]
    assert food_name in names, f'"{food_name}" not found in search results: {names}'


@then('the all-foods response should include "{food_name}"')
def step_all_foods_include(context, food_name):
    data = json.loads(context.response.content)
    names = [f['name'] for f in data.get('foods', [])]
    assert food_name in names, f'"{food_name}" not found in all-foods: {names}'


@then("the today_string context should match today's date")
def step_today_string_matches(context):
    expected = date.today().strftime('%Y-%m-%d')
    actual = context.response.context['today_string']
    assert actual == expected, f'Expected today_string={expected}, got {actual}'


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


@then('a meal with an auto-generated name should exist for date "{date_str}"')
def step_auto_generated_meal_exists(context, date_str):
    """Verify a meal was auto-generated with Breakfast/Lunch/Dinner name."""
    user = User.objects.get(username='nutrition@spotter.ai')
    meal = Meal.objects.filter(user=user, date=date_str).first()
    assert meal is not None, f'No meal found for {date_str}'
    assert meal.name in ['Breakfast', 'Lunch', 'Dinner'], (
        f'Meal name "{meal.name}" is not auto-generated (expected Breakfast/Lunch/Dinner)'
    )


@then('a food item named "{name}" with {calories:d} calories should exist')
def step_food_item_exists_check(context, name, calories):
    assert FoodItem.objects.filter(name=name, calories=calories).exists(), (
        f'FoodItem "{name}" ({calories} kcal) not found'
    )


@then('the food item should have {calories:d} calories')
def step_food_item_updated_calories(context, calories):
    context.current_food_item.refresh_from_db()
    assert context.current_food_item.calories == calories, (
        f'Expected {calories} calories, got {context.current_food_item.calories}'
    )


@then('the food item should have serving size {servings:d} and unit "{unit}"')
def step_food_item_serving_size(context, servings, unit):
    item = FoodItem.objects.filter(name=context.last_food_name).first()
    assert item is not None, f'No food item named "{context.last_food_name}" found'
    assert float(item.serving_size) == float(servings), (
        f'Expected serving_size={servings}, got {item.serving_size}'
    )
    assert item.serving_unit == unit, (
        f'Expected serving_unit="{unit}", got "{item.serving_unit}"'
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


# ── Saved items – Given steps ────────────────────────────────────────────────

@given('the food item is already saved')
def step_food_item_already_saved(context):
    user = User.objects.get(username='nutrition@spotter.ai')
    SavedFood.objects.get_or_create(
        user=user,
        name=context.current_food_item.name,
        defaults={'calories': context.current_food_item.calories},
    )


@given('I have a saved food item "{name}"')
def step_have_saved_food_item(context, name):
    user = User.objects.get(username='nutrition@spotter.ai')
    context.saved_food = SavedFood.objects.create(user=user, name=name, calories=100)


@given('I have a saved meal template "{name}" with {count:d} food items')
def step_have_saved_meal_template(context, name, count):
    user = User.objects.get(username='nutrition@spotter.ai')
    items = [
        {'type': 'food', 'name': f'Item {i}', 'calories': 100, 'protein': 0,
         'carbs': 0, 'fats': 0, 'serving_size': '1', 'serving_unit': 'serving'}
        for i in range(count)
    ]
    context.saved_meal = SavedMeal.objects.create(user=user, name=name, items=items)


# ── Saved items – When steps ─────────────────────────────────────────────────

@when('I save the food item via API')
def step_save_food_item_api(context):
    item = context.current_food_item
    context.response = context.test.client.post(
        '/nutrition/save_food_item/',
        data=json.dumps({
            'name': item.name,
            'calories': item.calories,
            'protein': item.protein,
            'carbs': item.carbs,
            'fats': item.fats,
            'serving_size': float(item.serving_size),
            'serving_unit': item.serving_unit,
        }),
        content_type='application/json',
    )


@when('I try to save a food item with calories {calories:d}')
def step_try_save_food_item_bad_calories(context, calories):
    context.response = context.test.client.post(
        '/nutrition/save_food_item/',
        data=json.dumps({
            'name': 'Bad Item',
            'calories': calories,
            'protein': 0,
            'carbs': 0,
            'fats': 0,
            'serving_size': 1.0,
            'serving_unit': 'serving',
        }),
        content_type='application/json',
    )


@when('I GET the save food item endpoint')
def step_get_save_food_item(context):
    context.response = context.test.client.get('/nutrition/save_food_item/')


@when('I save the meal as a template')
def step_save_meal_as_template(context):
    context.response = context.test.client.post(
        '/nutrition/save_meal_template/',
        data=json.dumps({'meal_id': context.current_meal.id}),
        content_type='application/json',
    )


@when('I add the saved food to that meal via ajax')
def step_add_saved_food_via_ajax(context):
    sf = context.saved_food
    context.response = context.test.client.post('/nutrition/add_food_item_ajax/', {
        'meal_id': context.current_meal.id,
        'food_name': sf.name,
        'food_calories': str(sf.calories),
        'protein': str(sf.protein),
        'carbs': str(sf.carbs),
        'fats': str(sf.fats),
        'serving_size': str(sf.serving_size),
        'serving_unit': sf.serving_unit,
    })


@when('I delete the saved food item')
def step_delete_saved_food_item(context):
    context.response = context.test.client.post(
        '/nutrition/delete_saved_item/',
        data=json.dumps({'type': 'food', 'id': context.saved_food.id}),
        content_type='application/json',
    )


@when('I add the saved meal to today')
def step_add_saved_meal_to_today(context):
    context.response = context.test.client.post(
        '/nutrition/add_saved_meal_to_date/',
        data=json.dumps({
            'saved_meal_id': context.saved_meal.id,
            'date': str(date.today()),
        }),
        content_type='application/json',
    )


# ── Saved items – Then steps ─────────────────────────────────────────────────

@then('a meal named "{name}" should exist for today')
def step_meal_exists_today_check(context, name):
    user = User.objects.get(username='nutrition@spotter.ai')
    assert Meal.objects.filter(user=user, name=name, date=date.today()).exists(), (
        f'Meal "{name}" for today not found'
    )


@then('the food item should be in my saved foods')
def step_food_item_in_saved_foods(context):
    user = User.objects.get(username='nutrition@spotter.ai')
    assert SavedFood.objects.filter(user=user, name=context.current_food_item.name).exists(), (
        f'SavedFood "{context.current_food_item.name}" not found'
    )


@then('the response should indicate already saved')
def step_response_already_saved(context):
    data = json.loads(context.response.content)
    assert data.get('already_saved') is True, f'Expected already_saved=True, got {data}'


@then('the meal template should be in my saved meals')
def step_meal_template_in_saved_meals(context):
    user = User.objects.get(username='nutrition@spotter.ai')
    assert SavedMeal.objects.filter(user=user, name=context.current_meal.name).exists(), (
        f'SavedMeal "{context.current_meal.name}" not found'
    )


@then('the saved food item should no longer exist')
def step_saved_food_item_deleted(context):
    assert not SavedFood.objects.filter(id=context.saved_food.id).exists(), (
        'SavedFood still exists after deletion'
    )
