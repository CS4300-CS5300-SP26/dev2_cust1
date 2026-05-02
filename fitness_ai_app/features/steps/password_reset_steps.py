"""Step definitions for password reset BDD scenarios."""

import uuid
from datetime import timedelta

from behave import given, when, then
from django.contrib.auth.models import User
from django.utils import timezone

from core.models import PasswordReset


# ── Given ──────────────────────────────────────────────────────────────────────

@given('a valid password reset token exists for "{email}"')
def step_valid_reset_token(context, email):
    user = User.objects.get(username=email)
    reset = PasswordReset.objects.create(user=user)
    context.reset_token = reset.token
    context.reset_user_email = email


@given('a used password reset token exists for "{email}"')
def step_used_reset_token(context, email):
    user = User.objects.get(username=email)
    reset = PasswordReset.objects.create(user=user, used=True)
    context.reset_token = reset.token
    context.reset_user_email = email


@given('an expired password reset token exists for "{email}"')
def step_expired_reset_token(context, email):
    user = User.objects.get(username=email)
    reset = PasswordReset.objects.create(user=user)
    # Backdate the created_at to 25 hours ago so it is expired
    PasswordReset.objects.filter(id=reset.id).update(
        created_at=timezone.now() - timedelta(hours=25)
    )
    reset.refresh_from_db()
    context.reset_token = reset.token
    context.reset_user_email = email


# ── When ──────────────────────────────────────────────────────────────────────

@when('I submit the forgot password form with email "{email}"')
def step_submit_forgot_password(context, email):
    context.response = context.test.client.post('/forgot_password/', {'email': email})


@when('I visit the reset password page for that token')
def step_visit_reset_password_page(context):
    context.response = context.test.client.get(f'/reset_password/{context.reset_token}/')


@when('I submit the reset password form with password "{password}"')
def step_submit_reset_password(context, password):
    context.response = context.test.client.post(
        f'/reset_password/{context.reset_token}/',
        {'password': password, 'confirm_password': password},
    )


# ── Then ──────────────────────────────────────────────────────────────────────

@then('I can log in as "{email}" with password "{password}"')
def step_can_log_in(context, email, password):
    user = User.objects.get(username=email)
    assert user.check_password(password), (
        f'Password for "{email}" was not updated to "{password}"'
    )
