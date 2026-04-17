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
        
        user = super().save_user(request, sociallogin, form)
        
        # Mark as social login user and ensure profile exists
        try:
            from .models import UserProfile
            profile, created = UserProfile.objects.get_or_create(user=user)
            if not profile.social_login_user:
                profile.social_login_user = True
                profile.save(update_fields=['social_login_user'])
        except:
            pass
        
        return user

    def pre_social_login(self, request, sociallogin):
        """
        Called after a successful social authentication but before login completes.
        
        This handles three scenarios:
        1. Auto-connect social account to existing user with same email
        2. Update existing user's email from social account data
        3. Set redirect URL for onboarding if needed
        
        IMPORTANT: For NEW users, the profile doesn't exist yet in pre_social_login,
        so we always redirect to onboarding for any new social signup.
        """
        super().pre_social_login(request, sociallogin)
        
        # ALWAYS redirect new social signups to onboarding
        # (sociallogin.user is not saved to DB yet for new users)
        if not sociallogin.is_existing:
            extra_data = sociallogin.account.extra_data or {}
            email = extra_data.get('email', '')
            
            if email:
                # Check if this email already exists
                try:
                    existing_user = User.objects.get(email__iexact=email)
                    # Existing user with this email - connect to them
                    sociallogin.connect(request, existing_user)
                except User.DoesNotExist:
                    # Try username as fallback
                    try:
                        existing_user = User.objects.get(username__iexact=email)
                        sociallogin.connect(request, existing_user)
                    except User.DoesNotExist:
                        # Brand new user - always send to onboarding
                        sociallogin.state['next'] = '/get_started_profile/'
                        return
            
            # We found an existing user to connect to, now check their onboarding status
            try:
                profile = sociallogin.user.profile
                if not profile.onboarding_completed:
                    sociallogin.state['next'] = '/get_started_profile/'
            except:
                # No profile exists yet, redirect to onboarding to create it
                sociallogin.state['next'] = '/get_started_profile/'
            return
        
        # If social account is already connected to a user, just update email if needed
        user = sociallogin.user
        extra_data = sociallogin.account.extra_data or {}
        email = extra_data.get('email', '')
        
        if email and not user.email:
            user.email = email
            user.save(update_fields=['email'])
        
        # For existing social accounts, check if user needs onboarding
        try:
            profile = user.profile
            if not profile.onboarding_completed:
                sociallogin.state['next'] = '/get_started_profile/'
        except:
            # No profile - redirect to create one
            sociallogin.state['next'] = '/get_started_profile/'

    def is_auto_signup_allowed(self, request, sociallogin):
        return True

