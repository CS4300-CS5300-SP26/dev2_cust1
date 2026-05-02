"""Step definitions for social river feed BDD scenarios."""

import json

from behave import given, when, then
from django.contrib.auth.models import User

from core.models import RiverEvent


def _get_river_user(context):
    return User.objects.get(username='riveruser@spotter.ai')


# ── Given ──────────────────────────────────────────────────────────────────────

@given('a river event titled "{title}" exists')
def step_river_event_exists(context, title):
    user = _get_river_user(context)
    context.current_river_event = RiverEvent.objects.create(
        user=user,
        event_type='workout_complete',
        title=title,
        detail='Test detail',
        rarity='common',
    )


# ── When ──────────────────────────────────────────────────────────────────────

@when('I post a comment "{text}" on that river event')
def step_post_comment(context, text):
    context.response = context.test.client.post(
        '/api/river/comment/',
        data=json.dumps({'event_id': context.current_river_event.id, 'text': text}),
        content_type='application/json',
    )


@when('I post an empty comment on that river event')
def step_post_empty_comment(context):
    context.response = context.test.client.post(
        '/api/river/comment/',
        data=json.dumps({'event_id': context.current_river_event.id, 'text': ''}),
        content_type='application/json',
    )


@when('I post a comment that is 301 characters long on that river event')
def step_post_long_comment(context):
    long_text = 'x' * 301
    context.response = context.test.client.post(
        '/api/river/comment/',
        data=json.dumps({'event_id': context.current_river_event.id, 'text': long_text}),
        content_type='application/json',
    )


@when('I post a comment "{text}" on river event id {event_id:d}')
def step_post_comment_nonexistent(context, text, event_id):
    context.response = context.test.client.post(
        '/api/river/comment/',
        data=json.dumps({'event_id': event_id, 'text': text}),
        content_type='application/json',
    )


@when('I spark that river event')
def step_spark_event(context):
    context.response = context.test.client.post(
        f'/api/river/spark/{context.current_river_event.id}/',
        content_type='application/json',
    )


@when('I spark that river event again')
def step_spark_event_again(context):
    context.response = context.test.client.post(
        f'/api/river/spark/{context.current_river_event.id}/',
        content_type='application/json',
    )


@when('I spark river event id {event_id:d}')
def step_spark_nonexistent_event(context, event_id):
    context.response = context.test.client.post(
        f'/api/river/spark/{event_id}/',
        content_type='application/json',
    )


# ── Then ──────────────────────────────────────────────────────────────────────

@then('the first river event has field "{field}"')
def step_first_event_has_field(context, field):
    data = json.loads(context.response.content)
    events = data.get('events', [])
    assert events, 'No events returned from river feed'
    assert field in events[0], (
        f'Field "{field}" missing from first event. Keys: {list(events[0].keys())}'
    )


@then('the sparked field is false')
def step_sparked_is_false(context):
    data = json.loads(context.response.content)
    assert data.get('sparked') is False, (
        f'Expected sparked=False, got: {data.get("sparked")}'
    )
