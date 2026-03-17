"""Step definitions for email verification BDD scenarios."""

import uuid
from datetime import timedelta

from behave import given, when, then
from django.contrib.auth.models import User
from django.utils import timezone

from core.models import EmailVerification


# ── Given steps ──────────────────────────────────────────────────────────────

@given('an unverified user "{email}" with a valid verification token')
def step_unverified_user_valid_token(context, email):
    User.objects.filter(username=email).delete()
    user = User.objects.create_user(
        username=email, email=email, password='testpass123', is_active=False
    )
    verification = EmailVerification.objects.create(user=user)
    context.verifications = getattr(context, 'verifications', {})
    context.verifications[email] = verification


@given('a user "{email}" whose token is already verified')
def step_already_verified_user(context, email):
    User.objects.filter(username=email).delete()
    user = User.objects.create_user(
        username=email, email=email, password='testpass123', is_active=True
    )
    verification = EmailVerification.objects.create(user=user, verified=True)
    context.verifications = getattr(context, 'verifications', {})
    context.verifications[email] = verification


@given('an unverified user "{email}" with an expired verification token')
def step_unverified_user_expired_token(context, email):
    User.objects.filter(username=email).delete()
    user = User.objects.create_user(
        username=email, email=email, password='testpass123', is_active=False
    )
    verification = EmailVerification.objects.create(user=user)
    verification.created_at = timezone.now() - timedelta(hours=25)
    verification.save()
    context.verifications = getattr(context, 'verifications', {})
    context.verifications[email] = verification


# ── When steps ───────────────────────────────────────────────────────────────

@when('I visit the verification link for "{email}"')
def step_visit_verification_link(context, email):
    verifications = getattr(context, 'verifications', {})
    token = verifications[email].token
    context.response = context.test.client.get(f'/verify_email/{token}/')


@when('I visit an invalid verification link')
def step_visit_invalid_link(context):
    context.response = context.test.client.get(f'/verify_email/{uuid.uuid4()}/')
