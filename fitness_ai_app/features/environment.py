"""
Behave environment configuration for Django integration.
Sets up the Django test environment for all BDD scenarios.
"""

from django.conf import settings


def before_all(context):
    """Use the in-memory email backend for all BDD scenarios."""
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
