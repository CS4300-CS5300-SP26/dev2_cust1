"""
Middleware to redirect social login users to onboarding if needed.
"""
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin


class SocialLoginOnboardingMiddleware(MiddlewareMixin):
    """
    Redirects social login users to /get_started_profile/ if they haven't
    completed onboarding yet and aren't already on that page.
    """
    
    def process_request(self, request):
        # Skip if not authenticated
        if not request.user.is_authenticated:
            return None
        
        # Skip if already on onboarding page
        if request.path == '/get_started_profile/':
            return None
        
        # Check if user needs onboarding
        try:
            profile = request.user.profile
            if profile.social_login_user and not profile.onboarding_completed:
                return redirect('get_started_profile')
        except:
            pass
        
        return None
