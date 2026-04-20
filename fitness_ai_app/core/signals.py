"""
Signals for social login handling and initial data population.
"""
from django.dispatch import receiver
from django.db.models.signals import post_migrate
from allauth.socialaccount.signals import social_account_updated
from django.contrib.auth.models import User
from .models import UserProfile


@receiver(social_account_updated)
def handle_social_account_updated(sender, request, sociallogin, **kwargs):
    """
    After a social account is updated/connected, mark the user as a social login user.
    """
    user = sociallogin.user
    try:
        profile, created = UserProfile.objects.get_or_create(user=user)
        if not profile.social_login_user:
            profile.social_login_user = True
            profile.save(update_fields=['social_login_user'])
    except:
        pass


@receiver(post_migrate)
def populate_databases(sender, **kwargs):
    """Auto-populate food and supplement databases after migrations."""
    if sender.name != 'core':
        return
    try:
        from django.core.management import call_command
        call_command('populate_food_database', verbosity=0)
        call_command('populate_supplements', verbosity=0)
    except Exception:
        pass

