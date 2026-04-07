from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth.models import User


class AutoSocialAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        
        # Get email from data first, then fall back to extra_data from social account
        email = data.get('email', '')
        if not email and sociallogin.account.extra_data:
            email = sociallogin.account.extra_data.get('email', '')
        
        # Set email on user if we found one
        if email:
            user.email = email
            if not user.username:
                user.username = email
        
        # Also set first_name/last_name from extra_data if not already set
        extra_data = sociallogin.account.extra_data or {}
        if not user.first_name:
            user.first_name = extra_data.get('given_name', '') or extra_data.get('first_name', '')
        if not user.last_name:
            user.last_name = extra_data.get('family_name', '') or extra_data.get('last_name', '')
        
        return user

    def save_user(self, request, sociallogin, form=None):
        """
        Override save_user to ensure email is properly saved from social login.
        """
        user = sociallogin.user
        
        # Get email from extra_data if not already set on user
        extra_data = sociallogin.account.extra_data or {}
        if not user.email:
            email = extra_data.get('email', '')
            if email:
                user.email = email
                if not user.username:
                    user.username = email
        
        return super().save_user(request, sociallogin, form)

    def pre_social_login(self, request, sociallogin):
        """
        Called after a successful social authentication but before login completes.
        
        This handles two scenarios:
        1. Auto-connect social account to existing user with same email
        2. Update existing user's email from social account data
        """
        super().pre_social_login(request, sociallogin)
        
        # If social account is already connected to a user, just update email if needed
        if sociallogin.is_existing:
            user = sociallogin.user
            extra_data = sociallogin.account.extra_data or {}
            email = extra_data.get('email', '')
            
            if email and not user.email:
                user.email = email
                user.save(update_fields=['email'])
            return
        
        # Social account is NOT connected yet - check if user with this email exists
        email = None
        extra_data = sociallogin.account.extra_data or {}
        email = extra_data.get('email', '')
        
        if not email:
            # No email from social provider, can't auto-connect
            return
        
        # Look for existing user with this email
        try:
            existing_user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            # Also check username (since we use email as username)
            try:
                existing_user = User.objects.get(username__iexact=email)
            except User.DoesNotExist:
                # No existing user found, allow normal signup flow
                return
        
        # Found existing user! Connect the social account to this user
        sociallogin.connect(request, existing_user)

    def is_auto_signup_allowed(self, request, sociallogin):
        return True
