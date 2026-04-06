from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class AutoSocialAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        email = data.get('email', '')
        if email and not user.username:
            user.username = email
        return user

    def is_auto_signup_allowed(self, request, sociallogin):
        return True
