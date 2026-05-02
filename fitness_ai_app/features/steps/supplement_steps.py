"""Step definitions for supplement tracking BDD scenarios."""

import json
from datetime import date

from behave import given, when, then
from django.contrib.auth.models import User

from core.models import Meal, MealSupplement, SupplementEntry


def _get_supp_user(context):
    return User.objects.get(username='suppuser@spotter.ai')


# ── Given ──────────────────────────────────────────────────────────────────────

@given('a supp meal named "{name}" exists for today')
def step_supp_meal_exists(context, name):
    user = _get_supp_user(context)
    context.current_meal = Meal.objects.create(user=user, name=name, date=date.today())


@given('a supplement "{name}" exists in that meal and is not taken')
def step_supplement_exists_not_taken(context, name):
    context.current_supplement = MealSupplement.objects.create(
        meal=context.current_meal,
        name=name,
        supplement_type='other',
        dosage='1',
        unit='serving',
        taken=False,
    )


@given('a taken supplement "{name}" exists in that meal')
def step_taken_supplement_exists(context, name):
    context.current_supplement = MealSupplement.objects.create(
        meal=context.current_meal,
        name=name,
        supplement_type='other',
        dosage='1',
        unit='serving',
        taken=True,
    )


@given('a standalone supplement entry "{name}" exists for today')
def step_standalone_supplement_exists(context, name):
    user = _get_supp_user(context)
    context.current_entry = SupplementEntry.objects.create(
        user=user,
        name=name,
        supplement_type='other',
        dosage='1',
        unit='serving',
        date=date.today(),
        taken=False,
    )


@given('another supp user has a supplement entry')
def step_other_supp_user_entry(context):
    other = User.objects.filter(username='other_suppuser@spotter.ai').first()
    if not other:
        other = User.objects.create_user(
            username='other_suppuser@spotter.ai',
            email='other_suppuser@spotter.ai',
            password='testpass123',
        )
    context.other_entry = SupplementEntry.objects.create(
        user=other,
        name='Other Supplement',
        supplement_type='other',
        dosage='1',
        unit='serving',
        date=date.today(),
        taken=False,
    )


# ── When ──────────────────────────────────────────────────────────────────────

@when('I add a supplement "{name}" to that meal')
def step_add_supplement_to_meal(context, name):
    context.response = context.test.client.post('/nutrition/add_supplement_to_meal/', {
        'meal_id': context.current_meal.id,
        'supplement_name': name,
        'supplement_type': 'other',
        'dosage': '1',
        'unit': 'serving',
        'date': date.today().strftime('%Y-%m-%d'),
    })


@when('I try to add a supplement with no name to that meal')
def step_add_supplement_no_name(context):
    context.response = context.test.client.post('/nutrition/add_supplement_to_meal/', {
        'meal_id': context.current_meal.id,
        'supplement_name': '',
        'supplement_type': 'other',
        'dosage': '1',
        'unit': 'serving',
        'date': date.today().strftime('%Y-%m-%d'),
    })


@when('I toggle that meal supplement')
def step_toggle_meal_supplement(context):
    context.response = context.test.client.post('/nutrition/toggle_meal_supplement/', {
        'supplement_id': context.current_supplement.id,
        'date': date.today().strftime('%Y-%m-%d'),
    })


@when('I delete that meal supplement')
def step_delete_meal_supplement(context):
    context.response = context.test.client.post('/nutrition/delete_meal_supplement/', {
        'supplement_id': context.current_supplement.id,
        'date': date.today().strftime('%Y-%m-%d'),
    })


@when('I GET "{url}"')
def step_get_url(context, url):
    context.response = context.test.client.get(url)


@when('I POST a supplement entry with name "{name}" for today')
def step_post_supplement_entry(context, name):
    context.response = context.test.client.post(
        '/api/supplement_entries/',
        data=json.dumps({
            'name': name,
            'supplement_type': 'other',
            'dosage': '1',
            'unit': 'serving',
            'date': date.today().strftime('%Y-%m-%d'),
        }),
        content_type='application/json',
    )


@when('I POST a supplement entry with no name')
def step_post_supplement_entry_no_name(context):
    context.response = context.test.client.post(
        '/api/supplement_entries/',
        data=json.dumps({'name': ''}),
        content_type='application/json',
    )


@when('I toggle that supplement entry taken status')
def step_toggle_supplement_entry(context):
    context.response = context.test.client.patch(
        f'/api/supplement_entries/{context.current_entry.id}/toggle/',
        data=json.dumps({'taken': True}),
        content_type='application/json',
    )


@when('I try to toggle the other user\'s supplement entry')
def step_toggle_other_supplement_entry(context):
    context.response = context.test.client.patch(
        f'/api/supplement_entries/{context.other_entry.id}/toggle/',
        data=json.dumps({'taken': True}),
        content_type='application/json',
    )


# ── Then ──────────────────────────────────────────────────────────────────────

@then('the supplement "{name}" should exist in the meal')
def step_supplement_exists_check(context, name):
    assert MealSupplement.objects.filter(meal=context.current_meal, name=name).exists(), (
        f'Supplement "{name}" not found in meal'
    )


@then('no meal supplement should exist in the meal')
def step_no_supplement_in_meal(context):
    assert not MealSupplement.objects.filter(meal=context.current_meal).exists()


@then('the supplement should be marked as taken')
def step_supplement_is_taken(context):
    context.current_supplement.refresh_from_db()
    assert context.current_supplement.taken, 'Supplement should be taken but is not'


@then('the supplement should be marked as not taken')
def step_supplement_not_taken(context):
    context.current_supplement.refresh_from_db()
    assert not context.current_supplement.taken, 'Supplement should not be taken but is'


@then('no supplement named "{name}" should exist in the meal')
def step_no_named_supplement_in_meal(context, name):
    assert not MealSupplement.objects.filter(meal=context.current_meal, name=name).exists(), (
        f'Supplement "{name}" should have been deleted but still exists'
    )
