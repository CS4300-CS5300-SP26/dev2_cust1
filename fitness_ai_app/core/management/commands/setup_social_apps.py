from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
import os


class Command(BaseCommand):
    help = 'Set up social authentication providers (Google, Apple, Facebook, Instagram)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Setting up social authentication apps...'))

        # Get or create the default site
        site = Site.objects.get_or_create(id=1)[0]

        # Google OAuth
        google_client_id = os.getenv('GOOGLE_CLIENT_ID', '')
        google_client_secret = os.getenv('GOOGLE_CLIENT_SECRET', '')

        if google_client_id and google_client_secret:
            google_app, created = SocialApp.objects.get_or_create(
                provider='google',
                defaults={
                    'name': 'Google',
                    'client_id': google_client_id,
                    'secret': google_client_secret,
                }
            )
            if not created:
                google_app.client_id = google_client_id
                google_app.secret = google_client_secret
                google_app.save()
            
            google_app.sites.set([site])
            status = 'created' if created else 'updated'
            self.stdout.write(self.style.SUCCESS(f'✓ Google OAuth {status}'))
        else:
            self.stdout.write(self.style.WARNING('⚠ Google credentials not found in .env'))

        # Apple OAuth (optional)
        apple_client_id = os.getenv('APPLE_CLIENT_ID', '')
        apple_client_secret = os.getenv('APPLE_CLIENT_SECRET', '')

        if apple_client_id and apple_client_secret:
            apple_app, created = SocialApp.objects.get_or_create(
                provider='apple',
                defaults={
                    'name': 'Apple',
                    'client_id': apple_client_id,
                    'secret': apple_client_secret,
                }
            )
            if not created:
                apple_app.client_id = apple_client_id
                apple_app.secret = apple_client_secret
                apple_app.save()
            
            apple_app.sites.set([site])
            status = 'created' if created else 'updated'
            self.stdout.write(self.style.SUCCESS(f'✓ Apple OAuth {status}'))

        # Facebook OAuth (optional)
        facebook_client_id = os.getenv('FACEBOOK_CLIENT_ID', '')
        facebook_client_secret = os.getenv('FACEBOOK_CLIENT_SECRET', '')

        if facebook_client_id and facebook_client_secret:
            facebook_app, created = SocialApp.objects.get_or_create(
                provider='facebook',
                defaults={
                    'name': 'Facebook',
                    'client_id': facebook_client_id,
                    'secret': facebook_client_secret,
                }
            )
            if not created:
                facebook_app.client_id = facebook_client_id
                facebook_app.secret = facebook_client_secret
                facebook_app.save()
            
            facebook_app.sites.set([site])
            status = 'created' if created else 'updated'
            self.stdout.write(self.style.SUCCESS(f'✓ Facebook OAuth {status}'))

        # Instagram OAuth (optional)
        instagram_client_id = os.getenv('INSTAGRAM_CLIENT_ID', '')
        instagram_client_secret = os.getenv('INSTAGRAM_CLIENT_SECRET', '')

        if instagram_client_id and instagram_client_secret:
            instagram_app, created = SocialApp.objects.get_or_create(
                provider='instagram',
                defaults={
                    'name': 'Instagram',
                    'client_id': instagram_client_id,
                    'secret': instagram_client_secret,
                }
            )
            if not created:
                instagram_app.client_id = instagram_client_id
                instagram_app.secret = instagram_client_secret
                instagram_app.save()
            
            instagram_app.sites.set([site])
            status = 'created' if created else 'updated'
            self.stdout.write(self.style.SUCCESS(f'✓ Instagram OAuth {status}'))

        self.stdout.write(self.style.SUCCESS('\n✅ Social authentication setup complete!'))
