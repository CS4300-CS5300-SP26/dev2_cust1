"""
Signals for social login handling.
"""
from django.dispatch import receiver
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
        # Ensure user profile exists and mark as social login user
        profile, created = UserProfile.objects.get_or_create(user=user)
        if not profile.social_login_user:
            profile.social_login_user = True
            profile.save(update_fields=['social_login_user'])
    except:
        pass

