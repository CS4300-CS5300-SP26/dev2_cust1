"""Step definitions for AI chat BDD scenarios."""

import json

from behave import given, when, then
from django.contrib.auth.models import User

from core.models import AIChatConversation


def _get_ai_user(context):
    return User.objects.get(username='aiuser@spotter.ai')


# ── Given ──────────────────────────────────────────────────────────────────────

@given('an AI chat conversation "{title}" exists for this user')
def step_ai_conversation_exists(context, title):
    user = _get_ai_user(context)
    context.current_conversation = AIChatConversation.objects.create(
        user=user, title=title
    )


@given('another AI user has a conversation')
def step_other_ai_user_conversation(context):
    other = User.objects.filter(username='other_aiuser@spotter.ai').first()
    if not other:
        other = User.objects.create_user(
            username='other_aiuser@spotter.ai',
            email='other_aiuser@spotter.ai',
            password='testpass123',
        )
    context.other_conversation = AIChatConversation.objects.create(
        user=other, title='Other Conversation'
    )


# ── When ──────────────────────────────────────────────────────────────────────

@when('I visit the chat history detail for that conversation')
def step_visit_chat_history_detail(context):
    context.response = context.test.client.get(
        f'/api/chat/history/{context.current_conversation.id}/'
    )


@when('I visit the chat history detail for the other user\'s conversation')
def step_visit_other_chat_history_detail(context):
    context.response = context.test.client.get(
        f'/api/chat/history/{context.other_conversation.id}/'
    )


# ── Then ──────────────────────────────────────────────────────────────────────

@then('the JSON "{key}" list is not empty')
def step_json_list_not_empty(context, key):
    if not hasattr(context, 'response_json'):
        context.response_json = json.loads(context.response.content)
    value = context.response_json[key]
    assert isinstance(value, list) and len(value) > 0, (
        f'Expected "{key}" to be a non-empty list, got: {value}'
    )
