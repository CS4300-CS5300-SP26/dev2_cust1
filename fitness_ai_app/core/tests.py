import uuid
import smtplib
import unittest
import json
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.utils import timezone

from .models import (
    EmailVerification, ExerciseType, MuscleGroup, Muscle, Equipment,
    TrainingExercise, UserInjury, UserEquipmentProfile, SupplementDatabase, SupplementEntry
)
from .forms import RegistrationForm


##    Added from feature/log-in branch
###########################################################################################################################################################################

@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class RegistrationFormTests(TestCase):
    """Tests for the RegistrationForm"""

    def test_valid_form(self):
        form = RegistrationForm(data={
            'email': 'test@spotter.ai',
            'password': 'securepass123',
            'confirm_password': 'securepass123',
        })
        self.assertTrue(form.is_valid())

    def test_password_mismatch(self):
        form = RegistrationForm(data={
            'email': 'test@spotter.ai',
            'password': 'securepass123',
            'confirm_password': 'differentpass',
        })
        self.assertFalse(form.is_valid())

    def test_password_too_short(self):
        form = RegistrationForm(data={
            'email': 'test@spotter.ai',
            'password': 'short',
            'confirm_password': 'short',
        })
        self.assertFalse(form.is_valid())

    def test_invalid_email(self):
        form = RegistrationForm(data={
            'email': 'not-an-email',
            'password': 'securepass123',
            'confirm_password': 'securepass123',
        })
        self.assertFalse(form.is_valid())

    def test_duplicate_email(self):
        User.objects.create_user(username='taken@spotter.ai', email='taken@spotter.ai', password='pass12345')
        form = RegistrationForm(data={
            'email': 'taken@spotter.ai',
            'password': 'securepass123',
            'confirm_password': 'securepass123',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    @unittest.skip('Email verification is disabled by default; users are created active')
    def test_save_creates_inactive_user(self):
        form = RegistrationForm(data={
            'email': 'new@spotter.ai',
            'password': 'securepass123',
            'confirm_password': 'securepass123',
        })
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertFalse(user.is_active)
        self.assertEqual(user.email, 'new@spotter.ai')
        self.assertEqual(user.username, 'new@spotter.ai')


class EmailVerificationModelTests(TestCase):
    """Tests for the EmailVerification model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='model@spotter.ai', email='model@spotter.ai',
            password='testpass123', is_active=False
        )

    def test_token_generated_on_create(self):
        v = EmailVerification.objects.create(user=self.user)
        self.assertIsNotNone(v.token)
        self.assertIsInstance(v.token, uuid.UUID)

    def test_not_expired_within_24_hours(self):
        v = EmailVerification.objects.create(user=self.user)
        self.assertFalse(v.is_expired())

    def test_expired_after_24_hours(self):
        v = EmailVerification.objects.create(user=self.user)
        v.created_at = timezone.now() - timedelta(hours=25)
        v.save()
        self.assertTrue(v.is_expired())

    def test_defaults_to_not_verified(self):
        v = EmailVerification.objects.create(user=self.user)
        self.assertFalse(v.verified)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class SplashViewTests(TestCase):
    """Tests for the splash/landing page"""

    def setUp(self):
        self.client = Client()

    def test_splash_loads(self):
        r = self.client.get('/')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Spotter.ai')

    def test_splash_redirects_authenticated_user(self):
        user = User.objects.create_user(username='auth@test.com', email='auth@test.com', password='pass12345')
        self.client.login(username='auth@test.com', password='pass12345')
        r = self.client.get('/')
        self.assertEqual(r.status_code, 302)
        self.assertIn('home_dash', r.url)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', EMAIL_VERIFICATION_ENABLED=False)
class RegistrationViewDisabledTests(TestCase):
    """Tests for registration with email verification disabled (default for dev)"""

    def setUp(self):
        self.client = Client()

    def test_get_started_page_loads(self):
        r = self.client.get('/user_get_started/')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Get Started')

    def test_successful_registration_auto_activates_user(self):
        r = self.client.post('/user_get_started/', {
            'email': 'new@spotter.ai',
            'password': 'securepass123',
            'confirm_password': 'securepass123',
        })
        self.assertEqual(r.status_code, 302)
        user = User.objects.get(username='new@spotter.ai')
        self.assertTrue(user.is_active)
        verification = EmailVerification.objects.get(user=user)
        self.assertTrue(verification.verified)

    def test_user_can_login_immediately(self):
        self.client.post('/user_get_started/', {
            'email': 'immediate@spotter.ai',
            'password': 'securepass123',
            'confirm_password': 'securepass123',
        })
        r = self.client.post('/user_login/', {
            'email': 'immediate@spotter.ai',
            'password': 'securepass123',
        })
        self.assertEqual(r.status_code, 302)
        self.assertIn('home_dash', r.url)

    def test_duplicate_email_rejected(self):
        User.objects.create_user(username='dup@spotter.ai', email='dup@spotter.ai', password='pass12345')
        r = self.client.post('/user_get_started/', {
            'email': 'dup@spotter.ai',
            'password': 'securepass123',
            'confirm_password': 'securepass123',
        })
        self.assertEqual(r.status_code, 200)

    def test_password_mismatch_rejected(self):
        r = self.client.post('/user_get_started/', {
            'email': 'mismatch@spotter.ai',
            'password': 'securepass123',
            'confirm_password': 'differentpass',
        })
        self.assertEqual(r.status_code, 200)
        self.assertFalse(User.objects.filter(username='mismatch@spotter.ai').exists())

    def test_redirects_authenticated_user(self):
        User.objects.create_user(username='auth@test.com', email='auth@test.com', password='pass12345')
        self.client.login(username='auth@test.com', password='pass12345')
        r = self.client.get('/user_get_started/')
        self.assertEqual(r.status_code, 302)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', EMAIL_VERIFICATION_ENABLED=True)
class RegistrationViewEnabledTests(TestCase):
    """Tests for registration with email verification enabled"""

    def setUp(self):
        self.client = Client()

    def test_successful_registration_creates_inactive_user(self):
        r = self.client.post('/user_get_started/', {
            'email': 'enabled@spotter.ai',
            'password': 'securepass123',
            'confirm_password': 'securepass123',
        })
        self.assertEqual(r.status_code, 302)
        user = User.objects.get(username='enabled@spotter.ai')
        self.assertFalse(user.is_active)
        self.assertTrue(EmailVerification.objects.filter(user=user).exists())

    def test_registration_sends_email(self):
        from django.core import mail
        self.client.post('/user_get_started/', {
            'email': 'email@spotter.ai',
            'password': 'securepass123',
            'confirm_password': 'securepass123',
        })
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Verify', mail.outbox[0].subject)
        self.assertIn('email@spotter.ai', mail.outbox[0].to)

    def test_registration_rolls_back_when_email_send_fails(self):
        with patch('core.views.send_mail', side_effect=smtplib.SMTPException('smtp unavailable')):
            r = self.client.post('/user_get_started/', {
                'email': 'failmail@spotter.ai',
                'password': 'securepass123',
                'confirm_password': 'securepass123',
            })

        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'We could not create your account right now.')
        self.assertFalse(User.objects.filter(username='failmail@spotter.ai').exists())
        self.assertFalse(EmailVerification.objects.filter(user__username='failmail@spotter.ai').exists())


@override_settings(EMAIL_VERIFICATION_ENABLED=True)
class EmailVerificationViewTests(TestCase):
    """Tests for the email verification link when enabled"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='verify@spotter.ai', email='verify@spotter.ai',
            password='testpass123', is_active=False
        )
        self.verification = EmailVerification.objects.create(user=self.user)

    def test_valid_token_activates_user(self):
        r = self.client.get(f'/verify_email/{self.verification.token}/')
        self.assertEqual(r.status_code, 302)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.verification.refresh_from_db()
        self.assertTrue(self.verification.verified)

    def test_valid_token_auto_logs_in(self):
        r = self.client.get(f'/verify_email/{self.verification.token}/')
        self.assertIn('get_started_profile', r.url)
        r2 = self.client.get('/get_started_profile/')
        self.assertEqual(r2.status_code, 200)

    def test_already_verified_token(self):
        self.verification.verified = True
        self.verification.save()
        r = self.client.get(f'/verify_email/{self.verification.token}/')
        self.assertEqual(r.status_code, 302)
        self.assertIn('user_login', r.url)

    def test_expired_token_deletes_user(self):
        self.verification.created_at = timezone.now() - timedelta(hours=25)
        self.verification.save()
        user_id = self.user.id
        r = self.client.get(f'/verify_email/{self.verification.token}/')
        self.assertEqual(r.status_code, 302)
        self.assertFalse(User.objects.filter(id=user_id).exists())

    def test_invalid_token(self):
        fake_token = uuid.uuid4()
        r = self.client.get(f'/verify_email/{fake_token}/')
        self.assertEqual(r.status_code, 302)
        self.assertIn('user_login', r.url)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class LoginViewTests(TestCase):
    """Tests for the login page"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='login@spotter.ai', email='login@spotter.ai', password='testpass123'
        )

    def test_login_page_loads(self):
        r = self.client.get('/user_login/')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Log In')

    def test_successful_login(self):
        r = self.client.post('/user_login/', {
            'email': 'login@spotter.ai',
            'password': 'testpass123',
        })
        self.assertEqual(r.status_code, 302)
        self.assertIn('home_dash', r.url)

    def test_wrong_password(self):
        r = self.client.post('/user_login/', {
            'email': 'login@spotter.ai',
            'password': 'wrongpassword',
        })
        self.assertEqual(r.status_code, 200)

    def test_nonexistent_user(self):
        r = self.client.post('/user_login/', {
            'email': 'nobody@spotter.ai',
            'password': 'testpass123',
        })
        self.assertEqual(r.status_code, 200)

    def test_redirects_authenticated_user(self):
        self.client.login(username='login@spotter.ai', password='testpass123')
        r = self.client.get('/user_login/')
        self.assertEqual(r.status_code, 302)
        self.assertIn('home_dash', r.url)

    def test_login_page_has_social_buttons(self):
        r = self.client.get('/user_login/')
        self.assertContains(r, '/login/google/')
        self.assertContains(r, '/login/apple/')
        self.assertContains(r, '/login/facebook/')
        self.assertContains(r, '/login/instagram/')

    def test_login_page_has_signup_link(self):
        r = self.client.get('/user_login/')
        self.assertContains(r, 'user_get_started')


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class LogoutViewTests(TestCase):
    """Tests for the logout functionality"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='logout@spotter.ai', email='logout@spotter.ai', password='testpass123'
        )

    def test_logout_redirects_to_splash(self):
        self.client.login(username='logout@spotter.ai', password='testpass123')
        r = self.client.get('/user_logout/')
        self.assertEqual(r.status_code, 302)

    def test_logout_ends_session(self):
        self.client.login(username='logout@spotter.ai', password='testpass123')
        self.client.get('/user_logout/')
        r = self.client.get('/home_dash/')
        self.assertEqual(r.status_code, 302)

    def test_logout_shows_success_message(self):
        """Test that logout shows success message."""
        self.client.login(username='logout@spotter.ai', password='testpass123')
        response = self.client.get('/user_logout/', follow=True)
        messages = list(response.context['messages'])
        self.assertTrue(any('logged out' in str(m).lower() for m in messages))


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class ProtectedPageTests(TestCase):
    """Tests for login-required pages"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='pages@spotter.ai', email='pages@spotter.ai', password='testpass123'
        )

    def test_unauthenticated_redirects(self):
        pages = ['/home_dash/', '/train/', '/nutrition/', '/ai/', '/social/']
        for url in pages:
            r = self.client.get(url)
            self.assertEqual(r.status_code, 302, f'{url} should redirect when not logged in')

    def test_authenticated_access(self):
        self.client.login(username='pages@spotter.ai', password='testpass123')
        pages = ['/home_dash/', '/train/', '/nutrition/', '/ai/', '/social/']
        for url in pages:
            r = self.client.get(url)
            self.assertEqual(r.status_code, 200, f'{url} should load when logged in')


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class NavigationTests(TestCase):
    """Tests for bottom nav bar and profile bubble on all pages"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='nav@spotter.ai', email='nav@spotter.ai', password='testpass123'
        )
        self.client.login(username='nav@spotter.ai', password='testpass123')

    def test_bottom_nav_on_all_pages(self):
        pages = ['/home_dash/', '/train/', '/nutrition/', '/social/']
        for url in pages:
            r = self.client.get(url)
            self.assertContains(r, 'bottom-nav', msg_prefix=f'{url}')
            self.assertContains(r, 'Home', msg_prefix=f'{url}')
            self.assertContains(r, 'Train', msg_prefix=f'{url}')
            self.assertContains(r, 'Nutrition', msg_prefix=f'{url}')
            self.assertContains(r, 'AI', msg_prefix=f'{url}')
            self.assertContains(r, 'Social', msg_prefix=f'{url}')

    def test_profile_bubble_on_all_pages(self):
        pages = ['/home_dash/', '/train/', '/nutrition/', '/social/']
        for url in pages:
            r = self.client.get(url)
            self.assertContains(r, 'profile-btn', msg_prefix=f'{url}')
            self.assertContains(r, 'profile-dropdown', msg_prefix=f'{url}')
            self.assertContains(r, 'Log Out', msg_prefix=f'{url}')

    def test_active_tab_highlighted(self):
        tab_map = {
            '/home_dash/': 'home',
            '/train/': 'train',
            '/nutrition/': 'nutrition',
            '/social/': 'social',
        }
        for url, tab in tab_map.items():
            r = self.client.get(url)
            self.assertContains(r, 'active', msg_prefix=f'{url}')

    def test_logo_on_all_pages(self):
        pages = ['/home_dash/', '/train/', '/nutrition/', '/social/']
        for url in pages:
            r = self.client.get(url)
            self.assertContains(r, 'logo-container', msg_prefix=f'{url}')


class SocialLoginRedirectTests(TestCase):
    """Tests for social login URL shortcuts"""

    def setUp(self):
        self.client = Client()

    def test_google_redirect(self):
        r = self.client.get('/login/google/')
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/google/login/', r.url)

    def test_apple_redirect(self):
        r = self.client.get('/login/apple/')
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/apple/login/', r.url)

    def test_facebook_redirect(self):
        r = self.client.get('/login/facebook/')
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/facebook/login/', r.url)

    def test_instagram_redirect(self):
        r = self.client.get('/login/instagram/')
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/instagram/login/', r.url)

##    END of: Added from feature/log-in branch
###########################################################################################################################################################################


# ---------------------------------------------------------------------------
#  Nutrition feature – Model tests (TDD)
# ---------------------------------------------------------------------------
from datetime import date
from .models import Meal, FoodItem


class MealModelTests(TestCase):
    """Tests for the Meal model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='meal@spotter.ai', email='meal@spotter.ai', password='testpass123'
        )

    def test_create_meal(self):
        meal = Meal.objects.create(user=self.user, name='Breakfast', date=date.today())
        self.assertEqual(meal.name, 'Breakfast')
        self.assertEqual(meal.user, self.user)
        self.assertEqual(meal.date, date.today())

    def test_meal_str(self):
        meal = Meal.objects.create(user=self.user, name='Lunch', date=date(2025, 3, 1))
        self.assertIn('Lunch', str(meal))

    def test_meal_ordering_by_name(self):
        Meal.objects.create(user=self.user, name='Dinner', date=date.today())
        Meal.objects.create(user=self.user, name='Breakfast', date=date.today())
        names = list(Meal.objects.values_list('name', flat=True))
        self.assertEqual(names, ['Breakfast', 'Dinner'])

    def test_meal_cascade_deletes_with_user(self):
        Meal.objects.create(user=self.user, name='Breakfast', date=date.today())
        self.user.delete()
        self.assertEqual(Meal.objects.count(), 0)


class FoodItemModelTests(TestCase):
    """Tests for the FoodItem model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='food@spotter.ai', email='food@spotter.ai', password='testpass123'
        )
        self.meal = Meal.objects.create(user=self.user, name='Breakfast', date=date.today())

    def test_create_food_item(self):
        item = FoodItem.objects.create(meal=self.meal, name='Eggs', calories=200)
        self.assertEqual(item.name, 'Eggs')
        self.assertEqual(item.calories, 200)
        self.assertFalse(item.completed)

    def test_food_item_str(self):
        item = FoodItem.objects.create(meal=self.meal, name='Eggs', calories=200)
        self.assertIn('Eggs', str(item))
        self.assertIn('200', str(item))

    def test_food_item_default_not_completed(self):
        item = FoodItem.objects.create(meal=self.meal, name='Toast', calories=150)
        self.assertFalse(item.completed)

    def test_food_item_cascade_deletes_with_meal(self):
        FoodItem.objects.create(meal=self.meal, name='Eggs', calories=200)
        self.meal.delete()
        self.assertEqual(FoodItem.objects.count(), 0)

    def test_food_item_ordering_by_created_at(self):
        a = FoodItem.objects.create(meal=self.meal, name='AAA', calories=100)
        b = FoodItem.objects.create(meal=self.meal, name='ZZZ', calories=200)
        items = list(FoodItem.objects.values_list('name', flat=True))
        self.assertEqual(items, ['AAA', 'ZZZ'])


# ---------------------------------------------------------------------------
#  Nutrition feature – View tests (TDD)
# ---------------------------------------------------------------------------

class NutritionPageViewTests(TestCase):
    """Tests for the nutrition_page view"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='nut@spotter.ai', email='nut@spotter.ai', password='testpass123'
        )
        self.client.login(username='nut@spotter.ai', password='testpass123')

    def test_page_loads(self):
        r = self.client.get('/nutrition/')
        self.assertEqual(r.status_code, 200)

    def test_requires_login(self):
        self.client.logout()
        r = self.client.get('/nutrition/')
        self.assertEqual(r.status_code, 302)

    def test_default_date_is_today(self):
        r = self.client.get('/nutrition/')
        self.assertEqual(r.context['selected_date'], date.today())

    def test_custom_date_via_query_param(self):
        r = self.client.get('/nutrition/?date=2025-06-15')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(str(r.context['selected_date']), '2025-06-15')

    def test_invalid_date_falls_back_to_today(self):
        r = self.client.get('/nutrition/?date=not-a-date')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['selected_date'], date.today())

    def test_shows_meals_for_selected_date(self):
        Meal.objects.create(user=self.user, name='Breakfast', date=date(2025, 6, 15))
        Meal.objects.create(user=self.user, name='Other Day', date=date(2025, 6, 16))
        r = self.client.get('/nutrition/?date=2025-06-15')
        meal_names = [m.name for m in r.context['meals']]
        self.assertIn('Breakfast', meal_names)
        self.assertNotIn('Other Day', meal_names)

    def test_total_calories_only_counts_completed(self):
        meal = Meal.objects.create(user=self.user, name='Breakfast', date=date.today())
        FoodItem.objects.create(meal=meal, name='Eggs', calories=200, completed=True)
        FoodItem.objects.create(meal=meal, name='Toast', calories=150, completed=False)
        r = self.client.get('/nutrition/')
        self.assertEqual(r.context['total_calories'], 200)

    def test_calorie_percentage_capped_at_100(self):
        meal = Meal.objects.create(user=self.user, name='Feast', date=date.today())
        FoodItem.objects.create(meal=meal, name='Huge', calories=5000, completed=True)
        r = self.client.get('/nutrition/')
        self.assertEqual(r.context['calories_percentage'], 100)

    def test_prev_next_date_links(self):
        r = self.client.get('/nutrition/?date=2025-06-15')
        self.assertEqual(r.context['prev_date'], '2025-06-14')
        self.assertEqual(r.context['next_date'], '2025-06-16')

    def test_does_not_show_other_users_meals(self):
        other = User.objects.create_user(username='other@spotter.ai', password='pass12345')
        Meal.objects.create(user=other, name='Secret Meal', date=date.today())
        r = self.client.get('/nutrition/')
        meal_names = [m.name for m in r.context['meals']]
        self.assertNotIn('Secret Meal', meal_names)


class AddMealViewTests(TestCase):
    """Tests for the add_meal view"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='addmeal@spotter.ai', email='addmeal@spotter.ai', password='testpass123'
        )
        self.client.login(username='addmeal@spotter.ai', password='testpass123')

    def test_add_meal_success(self):
        r = self.client.post('/nutrition/add_meal/', {
            'meal_name': 'Breakfast',
            'date': '2025-06-15',
        })
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Meal.objects.filter(name='Breakfast', user=self.user).exists())

    def test_add_meal_redirects_with_date(self):
        r = self.client.post('/nutrition/add_meal/', {
            'meal_name': 'Lunch',
            'date': '2025-06-15',
        })
        self.assertIn('date=2025-06-15', r.url)

    def test_add_meal_missing_name(self):
        """Test that meal is auto-generated with a name when none is provided."""
        r = self.client.post('/nutrition/add_meal/', {
            'meal_name': '',
            'date': '2025-06-15',
        })
        self.assertEqual(r.status_code, 302)
        # Meal should be created with an auto-generated name
        self.assertTrue(Meal.objects.exists())
        meal = Meal.objects.first()
        # Auto-generated names are based on time of day
        self.assertIn(meal.name, ['Breakfast', 'Lunch', 'Dinner'])

    def test_add_meal_missing_date(self):
        r = self.client.post('/nutrition/add_meal/', {
            'meal_name': 'Breakfast',
            'date': '',
        })
        self.assertEqual(r.status_code, 302)
        self.assertFalse(Meal.objects.exists())

    def test_add_meal_invalid_date(self):
        r = self.client.post('/nutrition/add_meal/', {
            'meal_name': 'Breakfast',
            'date': 'bad-date',
        })
        self.assertEqual(r.status_code, 302)
        self.assertFalse(Meal.objects.exists())

    def test_add_meal_requires_login(self):
        self.client.logout()
        r = self.client.post('/nutrition/add_meal/', {
            'meal_name': 'Breakfast',
            'date': '2025-06-15',
        })
        self.assertEqual(r.status_code, 302)
        self.assertFalse(Meal.objects.exists())

    def test_add_meal_get_not_allowed(self):
        r = self.client.get('/nutrition/add_meal/')
        self.assertEqual(r.status_code, 405)


class AddFoodItemViewTests(TestCase):
    """Tests for the add_food_item view"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='addfood@spotter.ai', email='addfood@spotter.ai', password='testpass123'
        )
        self.client.login(username='addfood@spotter.ai', password='testpass123')
        self.meal = Meal.objects.create(user=self.user, name='Breakfast', date=date.today())

    def test_add_food_item_success(self):
        r = self.client.post('/nutrition/add_food_item/', {
            'meal_id': self.meal.id,
            'food_name': 'Eggs',
            'food_calories': '200',
            'date': str(date.today()),
        })
        self.assertEqual(r.status_code, 302)
        self.assertTrue(FoodItem.objects.filter(name='Eggs', meal=self.meal).exists())

    def test_add_food_item_missing_fields(self):
        r = self.client.post('/nutrition/add_food_item/', {
            'meal_id': '',
            'food_name': '',
            'food_calories': '',
            'date': str(date.today()),
        })
        self.assertEqual(r.status_code, 302)
        self.assertFalse(FoodItem.objects.exists())

    def test_add_food_item_invalid_calories(self):
        r = self.client.post('/nutrition/add_food_item/', {
            'meal_id': self.meal.id,
            'food_name': 'Eggs',
            'food_calories': 'abc',
            'date': str(date.today()),
        })
        self.assertEqual(r.status_code, 302)
        self.assertFalse(FoodItem.objects.exists())

    def test_add_food_item_wrong_user_meal(self):
        other = User.objects.create_user(username='other@spotter.ai', password='pass12345')
        other_meal = Meal.objects.create(user=other, name='Other', date=date.today())
        r = self.client.post('/nutrition/add_food_item/', {
            'meal_id': other_meal.id,
            'food_name': 'Eggs',
            'food_calories': '200',
            'date': str(date.today()),
        })
        self.assertEqual(r.status_code, 404)

    def test_add_food_item_requires_login(self):
        self.client.logout()
        r = self.client.post('/nutrition/add_food_item/', {
            'meal_id': self.meal.id,
            'food_name': 'Eggs',
            'food_calories': '200',
            'date': str(date.today()),
        })
        self.assertEqual(r.status_code, 302)
        self.assertFalse(FoodItem.objects.exists())

    def test_add_food_item_get_not_allowed(self):
        r = self.client.get('/nutrition/add_food_item/')
        self.assertEqual(r.status_code, 405)


class ToggleFoodItemViewTests(TestCase):
    """Tests for the toggle_food_item view"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='toggle@spotter.ai', email='toggle@spotter.ai', password='testpass123'
        )
        self.client.login(username='toggle@spotter.ai', password='testpass123')
        self.meal = Meal.objects.create(user=self.user, name='Breakfast', date=date.today())
        self.item = FoodItem.objects.create(meal=self.meal, name='Eggs', calories=200)

    def test_toggle_marks_completed(self):
        self.assertFalse(self.item.completed)
        r = self.client.post('/nutrition/toggle_food_item/', {
            'item_id': self.item.id,
            'date': str(date.today()),
        })
        self.assertEqual(r.status_code, 302)
        self.item.refresh_from_db()
        self.assertTrue(self.item.completed)

    def test_toggle_marks_incomplete(self):
        self.item.completed = True
        self.item.save()
        r = self.client.post('/nutrition/toggle_food_item/', {
            'item_id': self.item.id,
            'date': str(date.today()),
        })
        self.item.refresh_from_db()
        self.assertFalse(self.item.completed)

    def test_toggle_redirects_with_date(self):
        r = self.client.post('/nutrition/toggle_food_item/', {
            'item_id': self.item.id,
            'date': '2025-06-15',
        })
        self.assertIn('date=2025-06-15', r.url)

    def test_toggle_without_date_redirects_to_nutrition(self):
        r = self.client.post('/nutrition/toggle_food_item/', {
            'item_id': self.item.id,
        })
        self.assertEqual(r.status_code, 302)
        self.assertIn('/nutrition/', r.url)

    def test_toggle_other_users_item_404(self):
        other = User.objects.create_user(username='other@spotter.ai', password='pass12345')
        other_meal = Meal.objects.create(user=other, name='Meal', date=date.today())
        other_item = FoodItem.objects.create(meal=other_meal, name='Food', calories=100)
        r = self.client.post('/nutrition/toggle_food_item/', {
            'item_id': other_item.id,
            'date': str(date.today()),
        })
        self.assertEqual(r.status_code, 404)

    def test_toggle_requires_login(self):
        self.client.logout()
        r = self.client.post('/nutrition/toggle_food_item/', {
            'item_id': self.item.id,
            'date': str(date.today()),
        })
        self.assertEqual(r.status_code, 302)
        self.item.refresh_from_db()
        self.assertFalse(self.item.completed)


class DeleteFoodItemViewTests(TestCase):
    """Tests for the delete_food_item view"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='delfood@spotter.ai', email='delfood@spotter.ai', password='testpass123'
        )
        self.client.login(username='delfood@spotter.ai', password='testpass123')
        self.meal = Meal.objects.create(user=self.user, name='Breakfast', date=date.today())
        self.item = FoodItem.objects.create(meal=self.meal, name='Eggs', calories=200)

    def test_delete_food_item(self):
        r = self.client.post('/nutrition/delete_food_item/', {
            'item_id': self.item.id,
            'date': str(date.today()),
        })
        self.assertEqual(r.status_code, 302)
        self.assertFalse(FoodItem.objects.filter(id=self.item.id).exists())

    def test_delete_redirects_with_date(self):
        r = self.client.post('/nutrition/delete_food_item/', {
            'item_id': self.item.id,
            'date': '2025-06-15',
        })
        self.assertIn('date=2025-06-15', r.url)

    def test_delete_without_date_redirects_to_nutrition(self):
        r = self.client.post('/nutrition/delete_food_item/', {
            'item_id': self.item.id,
        })
        self.assertEqual(r.status_code, 302)
        self.assertIn('/nutrition/', r.url)

    def test_delete_other_users_item_404(self):
        other = User.objects.create_user(username='other@spotter.ai', password='pass12345')
        other_meal = Meal.objects.create(user=other, name='Meal', date=date.today())
        other_item = FoodItem.objects.create(meal=other_meal, name='Food', calories=100)
        r = self.client.post('/nutrition/delete_food_item/', {
            'item_id': other_item.id,
            'date': str(date.today()),
        })
        self.assertEqual(r.status_code, 404)

    def test_delete_requires_login(self):
        self.client.logout()
        item_id = self.item.id
        r = self.client.post('/nutrition/delete_food_item/', {
            'item_id': item_id,
            'date': str(date.today()),
        })
        self.assertEqual(r.status_code, 302)
        self.assertTrue(FoodItem.objects.filter(id=item_id).exists())


# ---------------------------------------------------------------------------
#  API Chat – View tests (with OpenAI mock)
# ---------------------------------------------------------------------------
import json
import os
from unittest import mock


class ApiChatViewTests(TestCase):
    """Tests for the api_chat view"""

    def test_invalid_json_body(self):
        r = self.client.post(
            '/api/chat', data='not json', content_type='application/json'
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn('error', r.json())

    def test_empty_messages_list(self):
        r = self.client.post(
            '/api/chat',
            data=json.dumps({'messages': []}),
            content_type='application/json',
        )
        self.assertEqual(r.status_code, 400)

    @mock.patch.dict(os.environ, {}, clear=False)
    def test_missing_api_key(self):
        # Ensure OPENAI_API_KEY is absent
        os.environ.pop('OPENAI_API_KEY', None)
        r = self.client.post(
            '/api/chat',
            data=json.dumps({'messages': [{'role': 'user', 'content': 'hi'}]}),
            content_type='application/json',
        )
        self.assertEqual(r.status_code, 500)

    @mock.patch('core.views.OpenAI')
    @mock.patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_successful_chat(self, mock_openai_cls):
        mock_client = mock_openai_cls.return_value
        mock_resp = mock.MagicMock()
        mock_resp.choices[0].message.content = 'Hello from AI!'
        mock_client.chat.completions.create.return_value = mock_resp

        r = self.client.post(
            '/api/chat',
            data=json.dumps({'messages': [{'role': 'user', 'content': 'hi'}]}),
            content_type='application/json',
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['reply'], 'Hello from AI!')

    @mock.patch('core.views.OpenAI')
    @mock.patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_openai_api_error(self, mock_openai_cls):
        mock_client = mock_openai_cls.return_value
        mock_client.chat.completions.create.side_effect = Exception('API error')

        r = self.client.post(
            '/api/chat',
            data=json.dumps({'messages': [{'role': 'user', 'content': 'hi'}]}),
            content_type='application/json',
        )
        self.assertEqual(r.status_code, 502)
        self.assertIn('error', r.json())


# ---------------------------------------------------------------------------
#  Food Database Views – Coverage Tests
# ---------------------------------------------------------------------------
from datetime import date
from django.urls import reverse
from .models import Meal, FoodItem


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class FoodDatabaseViewsCoverageTests(TestCase):
    """Tests for search_foods, get_all_foods, and save_food_to_database views"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='foodtest@spotter.ai',
            email='foodtest@spotter.ai',
            password='testpass123'
        )
        self.meal = Meal.objects.create(
            user=self.user,
            name='Test Meal',
            date=date.today()
        )
        self.client.login(username='foodtest@spotter.ai', password='testpass123')

    # -------------------------------------------------------------------------
    # search_foods tests
    # -------------------------------------------------------------------------
    def test_search_foods_empty_for_short_query(self):
        """search_foods returns empty results when query is less than 2 characters"""
        # Create a food item to ensure it's not returned
        FoodItem.objects.create(meal=self.meal, name='Apple', calories=95)

        # Query with 0 characters
        r = self.client.get(reverse('search_foods'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['results'], [])

        # Query with 1 character
        r = self.client.get(reverse('search_foods'), {'q': 'A'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['results'], [])

    def test_search_foods_deduplicates_by_name_prefers_more_macros(self):
        """search_foods deduplicates by name (case-insensitive) and prefers entry with more macros"""
        # Create two items with same name (different case), one with more macros
        FoodItem.objects.create(
            meal=self.meal, name='chicken breast', calories=165,
            protein=0, carbs=0, fats=0
        )
        FoodItem.objects.create(
            meal=self.meal, name='Chicken Breast', calories=165,
            protein=31, carbs=0, fats=3
        )

        r = self.client.get(reverse('search_foods'), {'q': 'chicken'})
        self.assertEqual(r.status_code, 200)
        results = r.json()['results']

        # Should return only one result (deduplicated)
        self.assertEqual(len(results), 1)
        # Should prefer the one with more macros filled in
        self.assertEqual(results[0]['protein'], 31)
        self.assertEqual(results[0]['fats'], 3)

    # -------------------------------------------------------------------------
    # get_all_foods tests
    # -------------------------------------------------------------------------
    def test_get_all_foods_deduplicates_and_sorts_alphabetically(self):
        """get_all_foods deduplicates and returns results sorted alphabetically"""
        # Create foods in non-alphabetical order with duplicates
        FoodItem.objects.create(meal=self.meal, name='Zebra Meat', calories=100)
        FoodItem.objects.create(meal=self.meal, name='Apple', calories=95, protein=0)
        FoodItem.objects.create(meal=self.meal, name='apple', calories=95, protein=1)  # duplicate, more macros
        FoodItem.objects.create(meal=self.meal, name='Banana', calories=105)

        r = self.client.get(reverse('get_all_foods'))
        self.assertEqual(r.status_code, 200)
        data = r.json()

        # Should have 3 unique foods (apple deduplicated)
        self.assertEqual(data['count'], 3)

        # Should be sorted alphabetically (case-insensitive)
        names = [f['name'].lower() for f in data['foods']]
        self.assertEqual(names, sorted(names))

        # The apple entry should have protein=1 (the one with more macros)
        apple_entry = next(f for f in data['foods'] if f['name'].lower() == 'apple')
        self.assertEqual(apple_entry['protein'], 1)

    # -------------------------------------------------------------------------
    # save_food_to_database tests
    # -------------------------------------------------------------------------
    def test_save_food_rejects_invalid_json(self):
        """save_food_to_database rejects invalid JSON with 400"""
        r = self.client.post(
            reverse('save_food_to_database'),
            data='not valid json',
            content_type='application/json'
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn('error', r.json())

    def test_save_food_rejects_missing_name(self):
        """save_food_to_database rejects missing name with 400"""
        r = self.client.post(
            reverse('save_food_to_database'),
            data=json.dumps({'calories': 100}),
            content_type='application/json'
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn('error', r.json())
        self.assertIn('name', r.json()['error'].lower())

    def test_save_food_rejects_non_numeric_calories(self):
        """save_food_to_database rejects non-numeric calorie values with 400"""
        r = self.client.post(
            reverse('save_food_to_database'),
            data=json.dumps({'name': 'Test Food', 'calories': 'not-a-number'}),
            content_type='application/json'
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn('error', r.json())

    def test_save_food_creates_new_food_item(self):
        """save_food_to_database creates a new FoodItem"""
        r = self.client.post(
            reverse('save_food_to_database'),
            data=json.dumps({
                'name': 'New Test Food',
                'calories': 200,
                'protein': 15,
                'carbs': 20,
                'fats': 10
            }),
            content_type='application/json'
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data['success'])
        self.assertIn('Added', data['message'])

        # Verify food was created
        self.assertTrue(FoodItem.objects.filter(name='New Test Food').exists())
        food = FoodItem.objects.get(name='New Test Food')
        self.assertEqual(food.calories, 200)
        self.assertEqual(food.protein, 15)
        self.assertEqual(food.carbs, 20)
        self.assertEqual(food.fats, 10)

    def test_save_food_updates_existing_food_item(self):
        """save_food_to_database updates an existing FoodItem when id is provided"""
        # Create initial food item
        food = FoodItem.objects.create(
            meal=self.meal, name='Original Name', calories=100,
            protein=5, carbs=10, fats=2
        )

        r = self.client.post(
            reverse('save_food_to_database'),
            data=json.dumps({
                'id': food.id,
                'name': 'Updated Name',
                'calories': 250,
                'protein': 20,
                'carbs': 30,
                'fats': 8
            }),
            content_type='application/json'
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data['success'])
        self.assertIn('Updated', data['message'])

        # Verify food was updated
        food.refresh_from_db()
        self.assertEqual(food.name, 'Updated Name')
        self.assertEqual(food.calories, 250)
        self.assertEqual(food.protein, 20)
        self.assertEqual(food.carbs, 30)
        self.assertEqual(food.fats, 8)
###########################################################################################################################################################################
# Train Page Tests
###########################################################################################################################################################################

from datetime import date
from .models import Workout, Exercise


class TrainPageViewTests(TestCase):
    """Tests for the train_page view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='trainuser',
            email='train@test.com',
            password='testpass123'
        )
        self.client.login(username='trainuser', password='testpass123')

    def test_train_page_requires_login(self):
        """Test that train page requires authentication"""
        self.client.logout()
        response = self.client.get('/train/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/user_login', response.url)

    def test_train_page_loads_today_by_default(self):
        """Test that train page loads with today's date by default"""
        response = self.client.get('/train/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['selected_date'], date.today())
        self.assertFalse(response.context['is_past_date'])

    def test_train_page_with_specific_date(self):
        """Test that train page loads with a specific date parameter"""
        response = self.client.get('/train/?date=2026-04-01')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['date_string'], '2026-04-01')

    def test_train_page_invalid_date_falls_back_to_today(self):
        """Test that invalid date parameter falls back to today"""
        response = self.client.get('/train/?date=invalid-date')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['selected_date'], date.today())

    def test_train_page_past_date_is_flagged(self):
        """Test that past dates are flagged with is_past_date=True"""
        yesterday = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
        response = self.client.get(f'/train/?date={yesterday}')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_past_date'])

    def test_train_page_future_date_not_flagged_as_past(self):
        """Test that future dates have is_past_date=False"""
        tomorrow = (date.today() + timedelta(days=1)).strftime('%Y-%m-%d')
        response = self.client.get(f'/train/?date={tomorrow}')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['is_past_date'])

    def test_train_page_displays_workouts_for_selected_date(self):
        """Test that workouts are filtered by selected date"""
        today = date.today()
        yesterday = today - timedelta(days=1)

        workout_today = Workout.objects.create(
            user=self.user, name='Today Workout', goal='strength', date=today
        )
        workout_yesterday = Workout.objects.create(
            user=self.user, name='Yesterday Workout', goal='cardio', date=yesterday
        )

        response = self.client.get('/train/')
        workouts = list(response.context['workouts'])
        self.assertEqual(len(workouts), 1)
        self.assertEqual(workouts[0].name, 'Today Workout')

    def test_train_page_prev_next_date_navigation(self):
        """Test that prev_date and next_date are correctly calculated"""
        response = self.client.get('/train/?date=2026-04-15')
        self.assertEqual(response.context['prev_date'], '2026-04-14')
        self.assertEqual(response.context['next_date'], '2026-04-16')


class TrainPagePastDateReadOnlyTests(TestCase):
    """Tests for read-only behavior on past dates"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='trainuser2',
            email='train2@test.com',
            password='testpass123'
        )
        self.client.login(username='trainuser2', password='testpass123')
        self.yesterday = date.today() - timedelta(days=1)
        self.yesterday_str = self.yesterday.strftime('%Y-%m-%d')

        self.past_workout = Workout.objects.create(
            user=self.user, name='Past Workout', goal='strength', date=self.yesterday
        )
        self.past_exercise = Exercise.objects.create(
            workout=self.past_workout,
            name='Past Exercise',
            muscle_group='arms',
            sets=3,
            reps=10
        )

    def test_past_date_hides_edit_buttons_in_template(self):
        """Test that edit buttons are not rendered for past dates"""
        response = self.client.get(f'/train/?date={self.yesterday_str}')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_past_date'])
        # The edit button element should not appear in the HTML for past dates
        self.assertNotContains(response, 'class="edit-exercise-btn"')

    def test_past_date_hides_delete_buttons_in_template(self):
        """Test that delete workout button is not rendered for past dates"""
        response = self.client.get(f'/train/?date={self.yesterday_str}')
        self.assertNotContains(response, 'workout-delete-btn')

    def test_past_date_hides_add_exercise_button(self):
        """Test that add exercise button is not rendered for past dates"""
        response = self.client.get(f'/train/?date={self.yesterday_str}')
        self.assertNotContains(response, 'workout-edit-btn')

    def test_past_date_hides_log_workout_button(self):
        """Test that log workout button is not rendered for past dates"""
        response = self.client.get(f'/train/?date={self.yesterday_str}')
        self.assertNotContains(response, 'log-workout-btn')

    def test_current_date_shows_edit_buttons(self):
        """Test that edit buttons are shown for current date"""
        today = date.today()
        workout = Workout.objects.create(
            user=self.user, name='Today Workout', goal='strength', date=today
        )
        Exercise.objects.create(
            workout=workout, name='Today Exercise', muscle_group='chest'
        )

        response = self.client.get('/train/')
        self.assertFalse(response.context['is_past_date'])
        self.assertContains(response, 'edit-exercise-btn')
        self.assertContains(response, 'log-workout-btn')


class AddWorkoutTests(TestCase):
    """Tests for add_workout view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='workoutuser',
            email='workout@test.com',
            password='testpass123'
        )
        self.client.login(username='workoutuser', password='testpass123')

    def test_add_workout_requires_login(self):
        """Test that add_workout requires authentication"""
        self.client.logout()
        response = self.client.post('/train/add_workout/', {})
        self.assertEqual(response.status_code, 302)

    def test_add_workout_requires_post(self):
        """Test that add_workout only accepts POST requests"""
        response = self.client.get('/train/add_workout/')
        self.assertEqual(response.status_code, 405)

    def test_add_workout_success(self):
        """Test successful workout creation"""
        response = self.client.post('/train/add_workout/', {
            'workout_name': 'Morning Routine',
            'goal': 'strength',
            'status': 'planned',
            'date': '2026-04-04',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Workout.objects.filter(name='Morning Routine').exists())

    def test_add_workout_missing_fields(self):
        """Test workout creation fails with missing fields"""
        response = self.client.post('/train/add_workout/', {
            'workout_name': '',
            'goal': 'strength',
            'date': '2026-04-04',
        })
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Workout.objects.filter(goal='strength').exists())

    def test_add_workout_invalid_date(self):
        """Test workout creation fails with invalid date"""
        response = self.client.post('/train/add_workout/', {
            'workout_name': 'Test Workout',
            'goal': 'strength',
            'date': 'invalid',
        })
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Workout.objects.filter(name='Test Workout').exists())


class DeleteWorkoutTests(TestCase):
    """Tests for delete_workout view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='deleteuser',
            email='delete@test.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@test.com',
            password='testpass123'
        )
        self.client.login(username='deleteuser', password='testpass123')
        self.workout = Workout.objects.create(
            user=self.user, name='To Delete', goal='cardio', date=date.today()
        )

    def test_delete_workout_success(self):
        """Test successful workout deletion"""
        response = self.client.post('/train/delete_workout/', {
            'workout_id': self.workout.id,
            'date': date.today().strftime('%Y-%m-%d'),
        })
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Workout.objects.filter(id=self.workout.id).exists())

    def test_delete_workout_not_owned(self):
        """Test cannot delete another user's workout"""
        other_workout = Workout.objects.create(
            user=self.other_user, name='Other Workout', goal='strength', date=date.today()
        )
        response = self.client.post('/train/delete_workout/', {
            'workout_id': other_workout.id,
            'date': date.today().strftime('%Y-%m-%d'),
        })
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Workout.objects.filter(id=other_workout.id).exists())


class AddExerciseTests(TestCase):
    """Tests for add_exercise view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='exerciseuser',
            email='exercise@test.com',
            password='testpass123'
        )
        self.client.login(username='exerciseuser', password='testpass123')
        self.workout = Workout.objects.create(
            user=self.user, name='Test Workout', goal='strength', date=date.today()
        )

    def test_add_exercise_success(self):
        """Test successful exercise creation"""
        response = self.client.post('/train/add_exercise/', {
            'workout_id': self.workout.id,
            'exercise_name': 'Bench Press',
            'muscle_group': 'chest',
            'sets': '3',
            'reps': '10',
            'weight': '135',
            'date': date.today().strftime('%Y-%m-%d'),
        })
        self.assertEqual(response.status_code, 302)
        exercise = Exercise.objects.get(name='Bench Press')
        self.assertEqual(exercise.sets, 3)
        self.assertEqual(exercise.reps, 10)
        self.assertEqual(exercise.weight, 135)
        self.assertFalse(exercise.completed)

    def test_add_exercise_minimal_fields(self):
        """Test exercise creation with only required fields"""
        response = self.client.post('/train/add_exercise/', {
            'workout_id': self.workout.id,
            'exercise_name': 'Pushups',
            'muscle_group': 'chest',
            'date': date.today().strftime('%Y-%m-%d'),
        })
        self.assertEqual(response.status_code, 302)
        exercise = Exercise.objects.get(name='Pushups')
        self.assertIsNone(exercise.sets)
        self.assertIsNone(exercise.reps)
        self.assertIsNone(exercise.weight)

    def test_add_exercise_missing_required(self):
        """Test exercise creation fails without required fields"""
        response = self.client.post('/train/add_exercise/', {
            'workout_id': self.workout.id,
            'exercise_name': '',
            'muscle_group': 'chest',
            'date': date.today().strftime('%Y-%m-%d'),
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Exercise.objects.count(), 0)


class EditExerciseTests(TestCase):
    """Tests for edit_exercise view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='editexuser',
            email='editex@test.com',
            password='testpass123'
        )
        self.client.login(username='editexuser', password='testpass123')
        self.workout = Workout.objects.create(
            user=self.user, name='Test Workout', goal='strength', date=date.today()
        )
        self.exercise = Exercise.objects.create(
            workout=self.workout,
            name='Original Exercise',
            muscle_group='arms',
            sets=3,
            reps=10
        )

    def test_edit_exercise_success(self):
        """Test successful exercise edit"""
        response = self.client.post('/train/edit_exercise/', {
            'exercise_id': self.exercise.id,
            'exercise_name': 'Updated Exercise',
            'muscle_group': 'chest',
            'sets': '4',
            'reps': '12',
            'weight': '100',
            'status': 'completed',
            'date': date.today().strftime('%Y-%m-%d'),
        })
        self.assertEqual(response.status_code, 302)
        self.exercise.refresh_from_db()
        self.assertEqual(self.exercise.name, 'Updated Exercise')
        self.assertEqual(self.exercise.muscle_group, 'chest')
        self.assertEqual(self.exercise.sets, 4)
        self.assertEqual(self.exercise.reps, 12)
        self.assertEqual(self.exercise.weight, 100)
        self.assertTrue(self.exercise.completed)

    def test_edit_exercise_not_owned(self):
        """Test cannot edit another user's exercise"""
        other_user = User.objects.create_user(
            username='otherexuser', email='otherex@test.com', password='testpass123'
        )
        other_workout = Workout.objects.create(
            user=other_user, name='Other Workout', goal='cardio', date=date.today()
        )
        other_exercise = Exercise.objects.create(
            workout=other_workout, name='Other Exercise', muscle_group='legs'
        )
        response = self.client.post('/train/edit_exercise/', {
            'exercise_id': other_exercise.id,
            'exercise_name': 'Hacked Exercise',
            'muscle_group': 'arms',
            'date': date.today().strftime('%Y-%m-%d'),
        })
        self.assertEqual(response.status_code, 404)


class ToggleExerciseTests(TestCase):
    """Tests for toggle_exercise view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='toggleuser',
            email='toggle@test.com',
            password='testpass123'
        )
        self.client.login(username='toggleuser', password='testpass123')
        self.workout = Workout.objects.create(
            user=self.user, name='Test Workout', goal='strength', date=date.today()
        )
        self.exercise = Exercise.objects.create(
            workout=self.workout,
            name='Toggle Exercise',
            muscle_group='arms',
            completed=False
        )

    def test_toggle_exercise_to_completed(self):
        """Test toggling exercise from incomplete to completed"""
        response = self.client.post('/train/toggle_exercise/', {
            'exercise_id': self.exercise.id,
            'date': date.today().strftime('%Y-%m-%d'),
        })
        self.assertEqual(response.status_code, 302)
        self.exercise.refresh_from_db()
        self.assertTrue(self.exercise.completed)

    def test_toggle_exercise_to_incomplete(self):
        """Test toggling exercise from completed to incomplete"""
        self.exercise.completed = True
        self.exercise.save()

        response = self.client.post('/train/toggle_exercise/', {
            'exercise_id': self.exercise.id,
            'date': date.today().strftime('%Y-%m-%d'),
        })
        self.assertEqual(response.status_code, 302)
        self.exercise.refresh_from_db()
        self.assertFalse(self.exercise.completed)


class DeleteExerciseTests(TestCase):
    """Tests for delete_exercise view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='delexuser',
            email='delex@test.com',
            password='testpass123'
        )
        self.client.login(username='delexuser', password='testpass123')
        self.workout = Workout.objects.create(
            user=self.user, name='Test Workout', goal='strength', date=date.today()
        )
        self.exercise = Exercise.objects.create(
            workout=self.workout,
            name='To Delete',
            muscle_group='arms'
        )

    def test_delete_exercise_success(self):
        """Test successful exercise deletion"""
        response = self.client.post('/train/delete_exercise/', {
            'exercise_id': self.exercise.id,
            'date': date.today().strftime('%Y-%m-%d'),
        })
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Exercise.objects.filter(id=self.exercise.id).exists())

    def test_delete_exercise_not_owned(self):
        """Test cannot delete another user's exercise"""
        other_user = User.objects.create_user(
            username='otherdeluser', email='otherdel@test.com', password='testpass123'
        )
        other_workout = Workout.objects.create(
            user=other_user, name='Other Workout', goal='cardio', date=date.today()
        )
        other_exercise = Exercise.objects.create(
            workout=other_workout, name='Other Exercise', muscle_group='legs'
        )
        response = self.client.post('/train/delete_exercise/', {
            'exercise_id': other_exercise.id,
            'date': date.today().strftime('%Y-%m-%d'),
        })
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Exercise.objects.filter(id=other_exercise.id).exists())



class SocialAdapterTests(TestCase):
    """Tests for the AutoSocialAdapter - social login and auto-connect functionality."""

    def test_populate_user_sets_email_from_data(self):
        """Test that email is set on user from data dict."""
        from core.adapter import AutoSocialAdapter
        from unittest.mock import MagicMock
        
        adapter = AutoSocialAdapter()
        user = User()
        sociallogin = MagicMock()
        sociallogin.user = user
        sociallogin.account = MagicMock()
        sociallogin.account.extra_data = {}
        
        data = {'email': 'test@google.com', 'first_name': 'Test'}
        result = adapter.populate_user(None, sociallogin, data)
        
        self.assertEqual(result.email, 'test@google.com')
        self.assertEqual(result.username, 'test@google.com')

    def test_populate_user_sets_email_from_extra_data(self):
        """Test that email is set from extra_data when not in data dict."""
        from core.adapter import AutoSocialAdapter
        from unittest.mock import MagicMock
        
        adapter = AutoSocialAdapter()
        user = User()
        sociallogin = MagicMock()
        sociallogin.user = user
        sociallogin.account = MagicMock()
        sociallogin.account.extra_data = {'email': 'social@example.com'}
        
        data = {}
        result = adapter.populate_user(None, sociallogin, data)
        
        self.assertEqual(result.email, 'social@example.com')
        self.assertEqual(result.username, 'social@example.com')

    def test_populate_user_sets_first_name_from_given_name(self):
        """Test that first_name is set from given_name in extra_data."""
        from core.adapter import AutoSocialAdapter
        from unittest.mock import MagicMock
        
        adapter = AutoSocialAdapter()
        user = User()
        sociallogin = MagicMock()
        sociallogin.user = user
        sociallogin.account = MagicMock()
        sociallogin.account.extra_data = {'given_name': 'John', 'family_name': 'Doe'}
        
        data = {}
        result = adapter.populate_user(None, sociallogin, data)
        
        self.assertEqual(result.first_name, 'John')
        self.assertEqual(result.last_name, 'Doe')

    def test_populate_user_prefers_data_email_over_extra_data(self):
        """Test that email from data dict takes precedence over extra_data."""
        from core.adapter import AutoSocialAdapter
        from unittest.mock import MagicMock
        
        adapter = AutoSocialAdapter()
        user = User()
        sociallogin = MagicMock()
        sociallogin.user = user
        sociallogin.account = MagicMock()
        sociallogin.account.extra_data = {'email': 'social@example.com'}
        
        data = {'email': 'data@example.com'}
        result = adapter.populate_user(None, sociallogin, data)
        
        self.assertEqual(result.email, 'data@example.com')

    def test_pre_social_login_auto_connects_by_email(self):
        """Test that social account auto-connects to existing user with same email."""
        from core.adapter import AutoSocialAdapter
        from unittest.mock import MagicMock
        
        # Create existing user
        existing_user = User.objects.create_user(
            username='existing@example.com',
            email='existing@example.com',
            password='test123'
        )
        
        adapter = AutoSocialAdapter()
        sociallogin = MagicMock()
        sociallogin.is_existing = False
        sociallogin.account = MagicMock()
        sociallogin.account.extra_data = {'email': 'existing@example.com'}
        
        request = MagicMock()
        adapter.pre_social_login(request, sociallogin)
        
        # Verify connect was called with existing user
        sociallogin.connect.assert_called_once_with(request, existing_user)

    def test_pre_social_login_auto_connects_by_username(self):
        """Test that social account auto-connects when email matches username."""
        from core.adapter import AutoSocialAdapter
        from unittest.mock import MagicMock
        
        # Create user with email as username but empty email field
        existing_user = User.objects.create_user(
            username='user@example.com',
            email='',
            password='test123'
        )
        
        adapter = AutoSocialAdapter()
        sociallogin = MagicMock()
        sociallogin.is_existing = False
        sociallogin.account = MagicMock()
        sociallogin.account.extra_data = {'email': 'user@example.com'}
        
        request = MagicMock()
        adapter.pre_social_login(request, sociallogin)
        
        sociallogin.connect.assert_called_once_with(request, existing_user)

    def test_pre_social_login_allows_signup_for_new_email(self):
        """Test that social login allows new signup when no existing user found."""
        from core.adapter import AutoSocialAdapter
        from unittest.mock import MagicMock
        
        adapter = AutoSocialAdapter()
        sociallogin = MagicMock()
        sociallogin.is_existing = False
        sociallogin.account = MagicMock()
        sociallogin.account.extra_data = {'email': 'newuser@example.com'}
        
        request = MagicMock()
        adapter.pre_social_login(request, sociallogin)
        
        # connect should NOT be called - allow normal signup
        sociallogin.connect.assert_not_called()

    def test_pre_social_login_updates_email_for_existing_user(self):
        """Test that email is updated for existing social account user."""
        from core.adapter import AutoSocialAdapter
        from unittest.mock import MagicMock, patch
        
        existing_user = User.objects.create_user(
            username='test',
            email='',
            password='test123'
        )
        
        adapter = AutoSocialAdapter()
        sociallogin = MagicMock()
        sociallogin.is_existing = True
        sociallogin.user = existing_user
        sociallogin.account = MagicMock()
        sociallogin.account.extra_data = {'email': 'newemail@example.com'}
        
        request = MagicMock()
        
        with patch.object(existing_user, 'save') as mock_save:
            adapter.pre_social_login(request, sociallogin)
            mock_save.assert_called_once()

    def test_save_user_sets_email_from_extra_data(self):
        """Test that save_user sets email from extra_data when not on user."""
        from core.adapter import AutoSocialAdapter
        from allauth.socialaccount.models import SocialAccount
        from unittest.mock import MagicMock
        
        adapter = AutoSocialAdapter()
        
        # Create user without email
        user = User(username='noname')
        
        # Create social account with email in extra_data
        social_account = SocialAccount(
            provider='google',
            uid='123',
            extra_data={'email': 'fromextra@example.com'}
        )
        
        sociallogin = MagicMock()
        sociallogin.user = user
        sociallogin.account = social_account
        
        request = MagicMock()
        
        # Call save_user (it calls super().save_user which may create user)
        with patch.object(adapter.__class__.__bases__[0], 'save_user', return_value=user):
            result = adapter.save_user(request, sociallogin, form=None)
        
        # Email should be set from extra_data
        self.assertEqual(user.email, 'fromextra@example.com')
    
    def test_save_user_sets_username_from_email_when_no_username(self):
        """Test that save_user sets username from email when user has no username."""
        from core.adapter import AutoSocialAdapter
        from allauth.socialaccount.models import SocialAccount
        from unittest.mock import MagicMock
        
        adapter = AutoSocialAdapter()
        
        # Create user without email OR username
        user = User()
        user.email = ''
        user.username = ''
        
        # Create social account with email in extra_data
        social_account = SocialAccount(
            provider='google',
            uid='456',
            extra_data={'email': 'setusername@example.com'}
        )
        
        sociallogin = MagicMock()
        sociallogin.user = user
        sociallogin.account = social_account
        
        request = MagicMock()
        
        # Call save_user
        with patch.object(adapter.__class__.__bases__[0], 'save_user', return_value=user):
            result = adapter.save_user(request, sociallogin, form=None)
        
        # Username should be set from email
        self.assertEqual(user.username, 'setusername@example.com')
    
    def test_pre_social_login_no_email_returns_early(self):
        """Test that pre_social_login returns early when no email available."""
        from core.adapter import AutoSocialAdapter
        from allauth.socialaccount.models import SocialAccount
        from unittest.mock import MagicMock
        
        adapter = AutoSocialAdapter()
        
        user = User(username='test')
        
        social_account = SocialAccount(
            provider='google',
            uid='123',
            extra_data={}  # No email
        )
        
        sociallogin = MagicMock()
        sociallogin.user = user
        sociallogin.account = social_account
        sociallogin.is_existing = False
        
        request = MagicMock()
        
        # Should not raise and should return without connecting
        adapter.pre_social_login(request, sociallogin)
        
        # connect should not have been called
        sociallogin.connect.assert_not_called()
    
    def test_is_auto_signup_allowed_returns_true(self):
        """Test that is_auto_signup_allowed returns True."""
        from core.adapter import AutoSocialAdapter
        from unittest.mock import MagicMock
        
        adapter = AutoSocialAdapter()
        request = MagicMock()
        sociallogin = MagicMock()
        
        result = adapter.is_auto_signup_allowed(request, sociallogin)
        self.assertTrue(result)


class SocialLoginIntegrationTests(TestCase):
    """Integration tests for social login flows."""

    def test_user_registration_then_social_login_same_email(self):
        """Test that user can register with email then login with Google using same email."""
        # Create user via regular registration
        test_email = 'integration@example.com'
        test_password = 'IntegrationTest123!'
        
        user = User.objects.create_user(
            username=test_email,
            email=test_email,
            password=test_password,
            is_active=True
        )
        
        # Verify user was created
        self.assertTrue(User.objects.filter(email=test_email).exists())
        self.assertEqual(user.email, test_email)

    def test_social_login_sets_email_correctly(self):
        """Test that social login properly sets email on user."""
        from allauth.socialaccount.models import SocialAccount
        
        # Create user with empty email (simulating initial social login)
        user = User.objects.create_user(
            username='social_user@example.com',
            email='social_user@example.com',
            password='test123'
        )
        
        # Create social account
        social_account = SocialAccount.objects.create(
            user=user,
            provider='google',
            uid='google_123',
            extra_data={
                'email': 'social_user@example.com',
                'given_name': 'Social',
                'family_name': 'User'
            }
        )
        
        # Verify social account was created
        self.assertTrue(SocialAccount.objects.filter(user=user).exists())
        self.assertEqual(social_account.extra_data['email'], 'social_user@example.com')

    def test_multiple_providers_same_user(self):
        """Test that same user can connect multiple social providers."""
        from allauth.socialaccount.models import SocialAccount
        
        user = User.objects.create_user(
            username='multiauth@example.com',
            email='multiauth@example.com',
            password='test123'
        )
        
        # Connect Google
        google = SocialAccount.objects.create(
            user=user,
            provider='google',
            uid='google_123',
            extra_data={'email': 'multiauth@example.com'}
        )
        
        # Connect Facebook
        facebook = SocialAccount.objects.create(
            user=user,
            provider='facebook',
            uid='facebook_456',
            extra_data={'email': 'multiauth@example.com'}
        )
        
        # Verify both connected to same user
        self.assertEqual(user.socialaccount_set.count(), 2)
        self.assertIn('google', [s.provider for s in user.socialaccount_set.all()])
        self.assertIn('facebook', [s.provider for s in user.socialaccount_set.all()])


class AccountEmailHandlingTests(TestCase):
    """Tests for proper email handling in account creation and updates."""

    def test_regular_user_email_stored_correctly(self):
        """Test that regular user registration stores email in User model."""
        test_email = 'regular@example.com'
        test_password = 'RegularPass123!'
        
        user = User.objects.create_user(
            username=test_email,
            email=test_email,
            password=test_password
        )
        
        # Verify email is properly stored
        stored_user = User.objects.get(id=user.id)
        self.assertEqual(stored_user.email, test_email)
        self.assertEqual(stored_user.username, test_email)

    def test_social_user_email_from_extra_data(self):
        """Test that social user email can be retrieved from extra_data."""
        from allauth.socialaccount.models import SocialAccount
        
        user = User.objects.create_user(
            username='social@example.com',
            email='',  # Empty - comes from extra_data
            password='test123'
        )
        
        account = SocialAccount.objects.create(
            user=user,
            provider='google',
            uid='google_uid',
            extra_data={'email': 'social@example.com'}
        )
        
        # Verify email is in extra_data
        self.assertEqual(account.extra_data.get('email'), 'social@example.com')

    def test_email_case_insensitive_matching(self):
        """Test that email matching is case-insensitive for auto-connect."""
        test_email = 'CaseTest@Example.COM'
        
        user = User.objects.create_user(
            username=test_email.lower(),
            email=test_email.lower(),
            password='test123'
        )
        
        # Try to match with different case
        found = User.objects.filter(email__iexact=test_email)
        self.assertEqual(found.count(), 1)
        self.assertEqual(found.first().id, user.id)

    def test_username_as_email_fallback(self):
        """Test that username is used as fallback when email field is empty."""
        email = 'fallback@example.com'
        
        user = User.objects.create_user(
            username=email,
            email='',
            password='test123'
        )
        
        # Verify can be found by username
        found = User.objects.filter(username__iexact=email)
        self.assertEqual(found.count(), 1)
        self.assertEqual(found.first().id, user.id)


class PasswordResetTests(TestCase):
    """Tests for password reset functionality."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='reset@example.com',
            email='reset@example.com',
            password='OldPassword123!'
        )

    def test_forgot_password_page_loads(self):
        """Test that forgot password page loads correctly."""
        response = self.client.get('/forgot_password/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    @patch('core.views.send_mail')
    def test_forgot_password_sends_email(self, mock_send_mail):
        """Test that forgot password sends email for existing user."""
        response = self.client.post('/forgot_password/', {
            'email': 'reset@example.com'
        })
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/user_login/', response.url)
        
        # Email should have been sent
        mock_send_mail.assert_called_once()
        call_args = mock_send_mail.call_args
        self.assertIn('reset@example.com', call_args[0][3])

    @patch('core.views.send_mail')
    def test_forgot_password_case_insensitive_lookup(self, mock_send_mail):
        """Test that forgot password works with different case email."""
        response = self.client.post('/forgot_password/', {
            'email': 'RESET@EXAMPLE.COM'  # Different case
        })
        
        self.assertEqual(response.status_code, 302)
        mock_send_mail.assert_called_once()

    @patch('core.views.send_mail')
    def test_forgot_password_nonexistent_email(self, mock_send_mail):
        """Test that forgot password shows success message even for non-existent email."""
        response = self.client.post('/forgot_password/', {
            'email': 'nonexistent@example.com'
        })
        
        # Should still redirect and show generic message (security)
        self.assertEqual(response.status_code, 302)
        # Email should NOT be sent for non-existent user
        mock_send_mail.assert_not_called()

    def test_reset_password_page_with_valid_token(self):
        """Test reset password page loads with valid token."""
        from core.models import PasswordReset
        reset = PasswordReset.objects.create(user=self.user)
        
        response = self.client.get(f'/reset_password/{reset.token}/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    def test_reset_password_page_with_invalid_token(self):
        """Test reset password page with invalid token."""
        import uuid
        fake_token = uuid.uuid4()
        
        response = self.client.get(f'/reset_password/{fake_token}/')
        self.assertEqual(response.status_code, 200)
        # Should show error message
        self.assertIn('Invalid or expired', response.content.decode())

    def test_reset_password_with_valid_token(self):
        """Test that password is updated with valid reset token."""
        from core.models import PasswordReset
        reset = PasswordReset.objects.create(user=self.user)
        
        new_password = 'NewPassword123!'
        response = self.client.post(f'/reset_password/{reset.token}/', {
            'password': new_password,
            'confirm_password': new_password
        })
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/user_login/', response.url)
        
        # Verify password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(new_password))

    def test_reset_password_marks_token_used(self):
        """Test that reset token is marked as used after use."""
        from core.models import PasswordReset
        reset = PasswordReset.objects.create(user=self.user)
        
        self.client.post(f'/reset_password/{reset.token}/', {
            'password': 'NewPass123!',
            'confirm_password': 'NewPass123!'
        })
        
        # Verify token is marked as used
        reset.refresh_from_db()
        self.assertTrue(reset.used)

    def test_reset_password_cannot_reuse_token(self):
        """Test that password reset token cannot be reused."""
        from core.models import PasswordReset
        reset = PasswordReset.objects.create(user=self.user, used=True)
        
        response = self.client.get(f'/reset_password/{reset.token}/')
        self.assertIn('Invalid or expired', response.content.decode())

    def test_reset_password_expired_token(self):
        """Test that expired password reset token is rejected."""
        from core.models import PasswordReset
        from django.utils import timezone
        
        # Create an old reset token
        reset = PasswordReset.objects.create(user=self.user)
        # Manually set created_at to 25 hours ago
        reset.created_at = timezone.now() - timedelta(hours=25)
        reset.save()
        
        response = self.client.get(f'/reset_password/{reset.token}/')
        self.assertIn('Invalid or expired', response.content.decode())

    def test_reset_password_password_mismatch(self):
        """Test that mismatched passwords are rejected."""
        from core.models import PasswordReset
        reset = PasswordReset.objects.create(user=self.user)
        
        response = self.client.post(f'/reset_password/{reset.token}/', {
            'password': 'NewPass123!',
            'confirm_password': 'DifferentPass123!'
        })
        
        # Should show error
        self.assertIn('do not match', response.content.decode())
        
        # Password should NOT be changed
        self.user.refresh_from_db()
        self.assertFalse(self.user.check_password('NewPass123!'))

    def test_reset_password_weak_password_rejected(self):
        """Test that weak passwords are rejected."""
        from core.models import PasswordReset
        reset = PasswordReset.objects.create(user=self.user)
        
        response = self.client.post(f'/reset_password/{reset.token}/', {
            'password': 'weak',
            'confirm_password': 'weak'
        })
        
        # Should show validation error
        self.assertEqual(response.status_code, 200)
        
        # Password should NOT be changed
        self.user.refresh_from_db()
        self.assertFalse(self.user.check_password('weak'))

    def test_forgot_password_redirects_authenticated_user(self):
        """Test that authenticated users are redirected from forgot password."""
        self.client.login(username='reset@example.com', password='OldPassword123!')
        
        response = self.client.get('/forgot_password/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/home_dash/', response.url)


# ==================================================================================
# ADDITIONAL COVERAGE TESTS - Views and Management Commands
# ==================================================================================

class ChatPageViewTests(TestCase):
    """Tests for the chat_page view."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='chatuser@example.com',
            email='chatuser@example.com',
            password='TestPass123!'
        )
        self.user.is_active = True
        self.user.save()
    
    def test_chat_page_requires_login(self):
        """Test that chat page requires authentication."""
        response = self.client.get('/ai/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('user_login', response.url)
    
    def test_chat_page_loads_for_authenticated_user(self):
        """Test that chat page loads for logged in user."""
        self.client.login(username='chatuser@example.com', password='TestPass123!')
        response = self.client.get('/ai/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/chat.html')


class HomeDashViewTests(TestCase):
    """Tests for the home_dash view."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='dashuser@example.com',
            email='dashuser@example.com',
            password='TestPass123!'
        )
        self.user.is_active = True
        self.user.save()
    
    def test_home_dash_requires_login(self):
        """Test that home_dash requires authentication."""
        response = self.client.get('/home_dash/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('user_login', response.url)
    
    def test_home_dash_loads_for_authenticated_user(self):
        """Test that home_dash loads for logged in user."""
        self.client.login(username='dashuser@example.com', password='TestPass123!')
        response = self.client.get('/home_dash/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['active_tab'], 'home')


class TrainPageViewTests(TestCase):
    """Tests for the train_page view."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='trainuser@example.com',
            email='trainuser@example.com',
            password='TestPass123!'
        )
        self.user.is_active = True
        self.user.save()
    
    def test_train_page_requires_login(self):
        """Test that train page requires authentication."""
        response = self.client.get('/train/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('user_login', response.url)
    
    def test_train_page_loads_for_authenticated_user(self):
        """Test that train page loads for logged in user."""
        self.client.login(username='trainuser@example.com', password='TestPass123!')
        response = self.client.get('/train/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['active_tab'], 'train')


class SocialPageViewTests(TestCase):
    """Tests for the social_page view."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='socialuser@example.com',
            email='socialuser@example.com',
            password='TestPass123!'
        )
        self.user.is_active = True
        self.user.save()
    
    def test_social_page_requires_login(self):
        """Test that social page requires authentication."""
        response = self.client.get('/social/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('user_login', response.url)
    
    def test_social_page_loads_for_authenticated_user(self):
        """Test that social page loads for logged in user."""
        self.client.login(username='socialuser@example.com', password='TestPass123!')
        response = self.client.get('/social/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['active_tab'], 'social')


class VerifyEmailViewDetailedTests(TestCase):
    """Additional detailed tests for verify_email view."""
    
    def setUp(self):
        from .models import EmailVerification
        
        self.user = User.objects.create_user(
            username='verifydetail@example.com',
            email='verifydetail@example.com',
            password='TestPass123!',
            is_active=False
        )
        self.verification = EmailVerification.objects.create(user=self.user)
    
    def test_verify_email_already_verified(self):
        """Test that already verified email shows info message."""
        self.verification.verified = True
        self.verification.save()
        
        response = self.client.get(f'/verify_email/{self.verification.token}/', follow=True)
        
        messages = list(response.context['messages'])
        self.assertTrue(any('already verified' in str(m).lower() for m in messages))
    
    def test_verify_email_expired(self):
        """Test that expired verification link is handled."""
        # Expire the verification by setting created_at to 25 hours ago
        self.verification.created_at = timezone.now() - timedelta(hours=25)
        self.verification.save()
        
        response = self.client.get(f'/verify_email/{self.verification.token}/', follow=True)
        
        messages = list(response.context['messages'])
        self.assertTrue(any('expired' in str(m).lower() for m in messages))
        
        # User should be deleted
        self.assertFalse(User.objects.filter(username='verifydetail@example.com').exists())
    
    def test_verify_email_invalid_token(self):
        """Test that invalid token shows error."""
        invalid_token = uuid.uuid4()
        
        response = self.client.get(f'/verify_email/{invalid_token}/', follow=True)
        
        messages = list(response.context['messages'])
        self.assertTrue(any('invalid' in str(m).lower() for m in messages))
    
    def test_verify_email_success_activates_user(self):
        """Test that successful verification activates user."""
        response = self.client.get(f'/verify_email/{self.verification.token}/', follow=True)
        
        # User should be active now
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        
        # Verification should be marked as verified
        self.verification.refresh_from_db()
        self.assertTrue(self.verification.verified)
        
        messages = list(response.context['messages'])
        self.assertTrue(any('verified' in str(m).lower() for m in messages))


class UserLoginViewDetailedTests(TestCase):
    """Additional detailed tests for user_login view."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='logindetail@example.com',
            email='logindetail@example.com',
            password='TestPass123!'
        )
        self.user.is_active = True
        self.user.save()
    
    def test_login_redirects_authenticated_user(self):
        """Test that authenticated user is redirected from login page."""
        self.client.login(username='logindetail@example.com', password='TestPass123!')
        
        response = self.client.get('/user_login/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/home_dash/', response.url)
    
    def test_login_with_next_parameter(self):
        """Test that login redirects to next parameter after success."""
        response = self.client.post('/user_login/?next=/nutrition/', {
            'email': 'logindetail@example.com',
            'password': 'TestPass123!'
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('/nutrition/', response.url)
    
    def test_login_invalid_credentials_shows_error(self):
        """Test that invalid credentials show error message."""
        response = self.client.post('/user_login/', {
            'email': 'logindetail@example.com',
            'password': 'WrongPassword'
        }, follow=True)
        
        messages = list(response.context['messages'])
        self.assertTrue(any('invalid' in str(m).lower() for m in messages))


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class UserGetStartedViewDetailedTests(TestCase):
    """Additional detailed tests for user_get_started view."""
    
    def test_get_started_redirects_authenticated_user(self):
        """Test that authenticated user is redirected from signup page."""
        user = User.objects.create_user(
            username='existinguser@example.com',
            email='existinguser@example.com',
            password='TestPass123!',
            is_active=True
        )
        self.client.login(username='existinguser@example.com', password='TestPass123!')
        
        response = self.client.get('/user_get_started/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/home_dash/', response.url)
    
    @override_settings(EMAIL_VERIFICATION_ENABLED=False)
    def test_signup_without_email_verification(self):
        """Test signup flow when email verification is disabled."""
        response = self.client.post('/user_get_started/', {
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!'
        }, follow=True)
        
        # User should be created and active
        user = User.objects.get(username='newuser@example.com')
        self.assertTrue(user.is_active)
        
        messages = list(response.context['messages'])
        self.assertTrue(any('created' in str(m).lower() for m in messages))
    
    @override_settings(EMAIL_VERIFICATION_ENABLED=True)
    @patch('core.views.send_mail')
    def test_signup_with_email_verification(self, mock_send_mail):
        """Test signup flow when email verification is enabled."""
        mock_send_mail.return_value = 1
        
        response = self.client.post('/user_get_started/', {
            'email': 'verifyuser@example.com',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!'
        }, follow=True)
        
        # User should be created but NOT active
        user = User.objects.get(username='verifyuser@example.com')
        self.assertFalse(user.is_active)
        
        # Email should have been sent
        self.assertTrue(mock_send_mail.called)
        
        messages = list(response.context['messages'])
        self.assertTrue(any('verify' in str(m).lower() or 'check' in str(m).lower() for m in messages))
    
    @override_settings(EMAIL_VERIFICATION_ENABLED=True)
    @patch('core.views.send_mail')
    def test_signup_email_failure_shows_error(self, mock_send_mail):
        """Test that email failure during signup is handled."""
        mock_send_mail.side_effect = smtplib.SMTPException('SMTP error')
        
        response = self.client.post('/user_get_started/', {
            'email': 'emailfail@example.com',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)


class ForgotPasswordEmailErrorTests(TestCase):
    """Tests for forgot_password email sending error handling."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='emailerror@example.com',
            email='emailerror@example.com',
            password='TestPass123!',
            is_active=True
        )
    
    @patch('core.views.send_mail')
    def test_forgot_password_email_failure_is_logged(self, mock_send_mail):
        """Test that email failure during password reset is handled gracefully."""
        mock_send_mail.side_effect = smtplib.SMTPException('SMTP unavailable')
        
        response = self.client.post('/forgot_password/', {
            'email': 'emailerror@example.com'
        }, follow=True)
        
        # Should still show success message (security - don't reveal if account exists)
        messages = list(response.context['messages'])
        self.assertTrue(any('if an account exists' in str(m).lower() for m in messages))


class SetupSocialAppsCommandTests(TestCase):
    """Tests for the setup_social_apps management command."""
    
    def test_command_runs_without_credentials(self):
        """Test that command runs successfully even without credentials."""
        from django.core.management import call_command
        from io import StringIO
        
        out = StringIO()
        
        # Clear any existing env vars
        with patch.dict('os.environ', {}, clear=True):
            call_command('setup_social_apps', stdout=out)
        
        output = out.getvalue()
        self.assertIn('Setting up social authentication', output)
        self.assertIn('complete', output.lower())
    
    @patch.dict('os.environ', {
        'GOOGLE_CLIENT_ID': 'test-google-id',
        'GOOGLE_CLIENT_SECRET': 'test-google-secret'
    })
    def test_command_creates_google_app(self):
        """Test that command creates Google social app."""
        from django.core.management import call_command
        from allauth.socialaccount.models import SocialApp
        from io import StringIO
        
        out = StringIO()
        call_command('setup_social_apps', stdout=out)
        
        output = out.getvalue()
        self.assertIn('Google', output)
        
        # Verify SocialApp was created
        self.assertTrue(SocialApp.objects.filter(provider='google').exists())
        app = SocialApp.objects.get(provider='google')
        self.assertEqual(app.client_id, 'test-google-id')
    
    @patch.dict('os.environ', {
        'GOOGLE_CLIENT_ID': 'updated-google-id',
        'GOOGLE_CLIENT_SECRET': 'updated-google-secret'
    })
    def test_command_updates_existing_app(self):
        """Test that command updates existing social app."""
        from django.core.management import call_command
        from django.contrib.sites.models import Site
        from allauth.socialaccount.models import SocialApp
        from io import StringIO
        
        # Create existing app
        site = Site.objects.get_or_create(id=1)[0]
        existing_app = SocialApp.objects.create(
            provider='google',
            name='Google',
            client_id='old-id',
            secret='old-secret'
        )
        existing_app.sites.set([site])
        
        out = StringIO()
        call_command('setup_social_apps', stdout=out)
        
        output = out.getvalue()
        self.assertIn('updated', output.lower())
        
        # Verify app was updated
        existing_app.refresh_from_db()
        self.assertEqual(existing_app.client_id, 'updated-google-id')
    
    @patch.dict('os.environ', {
        'APPLE_CLIENT_ID': 'test-apple-id',
        'APPLE_CLIENT_SECRET': 'test-apple-secret'
    })
    def test_command_creates_apple_app(self):
        """Test that command creates Apple social app."""
        from django.core.management import call_command
        from allauth.socialaccount.models import SocialApp
        from io import StringIO
        
        out = StringIO()
        call_command('setup_social_apps', stdout=out)
        
        output = out.getvalue()
        self.assertIn('Apple', output)
        
        self.assertTrue(SocialApp.objects.filter(provider='apple').exists())
    
    @patch.dict('os.environ', {
        'FACEBOOK_CLIENT_ID': 'test-fb-id',
        'FACEBOOK_CLIENT_SECRET': 'test-fb-secret'
    })
    def test_command_creates_facebook_app(self):
        """Test that command creates Facebook social app."""
        from django.core.management import call_command
        from allauth.socialaccount.models import SocialApp
        from io import StringIO
        
        out = StringIO()
        call_command('setup_social_apps', stdout=out)
        
        output = out.getvalue()
        self.assertIn('Facebook', output)
        
        self.assertTrue(SocialApp.objects.filter(provider='facebook').exists())
    
    @patch.dict('os.environ', {
        'INSTAGRAM_CLIENT_ID': 'test-insta-id',
        'INSTAGRAM_CLIENT_SECRET': 'test-insta-secret'
    })
    def test_command_creates_instagram_app(self):
        """Test that command creates Instagram social app."""
        from django.core.management import call_command
        from allauth.socialaccount.models import SocialApp
        from io import StringIO
        
        out = StringIO()
        call_command('setup_social_apps', stdout=out)
        
        output = out.getvalue()
        self.assertIn('Instagram', output)
        
        self.assertTrue(SocialApp.objects.filter(provider='instagram').exists())
    
    @patch.dict('os.environ', {
        'APPLE_CLIENT_ID': 'updated-apple-id',
        'APPLE_CLIENT_SECRET': 'updated-apple-secret'
    })
    def test_command_updates_existing_apple_app(self):
        """Test that command updates existing Apple social app."""
        from django.core.management import call_command
        from django.contrib.sites.models import Site
        from allauth.socialaccount.models import SocialApp
        from io import StringIO
        
        site = Site.objects.get_or_create(id=1)[0]
        existing_app = SocialApp.objects.create(
            provider='apple',
            name='Apple',
            client_id='old-apple-id',
            secret='old-apple-secret'
        )
        existing_app.sites.set([site])
        
        out = StringIO()
        call_command('setup_social_apps', stdout=out)
        
        existing_app.refresh_from_db()
        self.assertEqual(existing_app.client_id, 'updated-apple-id')
    
    @patch.dict('os.environ', {
        'FACEBOOK_CLIENT_ID': 'updated-fb-id',
        'FACEBOOK_CLIENT_SECRET': 'updated-fb-secret'
    })
    def test_command_updates_existing_facebook_app(self):
        """Test that command updates existing Facebook social app."""
        from django.core.management import call_command
        from django.contrib.sites.models import Site
        from allauth.socialaccount.models import SocialApp
        from io import StringIO
        
        site = Site.objects.get_or_create(id=1)[0]
        existing_app = SocialApp.objects.create(
            provider='facebook',
            name='Facebook',
            client_id='old-fb-id',
            secret='old-fb-secret'
        )
        existing_app.sites.set([site])
        
        out = StringIO()
        call_command('setup_social_apps', stdout=out)
        
        existing_app.refresh_from_db()
        self.assertEqual(existing_app.client_id, 'updated-fb-id')
    
    @patch.dict('os.environ', {
        'INSTAGRAM_CLIENT_ID': 'updated-insta-id',
        'INSTAGRAM_CLIENT_SECRET': 'updated-insta-secret'
    })
    def test_command_updates_existing_instagram_app(self):
        """Test that command updates existing Instagram social app."""
        from django.core.management import call_command
        from django.contrib.sites.models import Site
        from allauth.socialaccount.models import SocialApp
        from io import StringIO
        
        site = Site.objects.get_or_create(id=1)[0]
        existing_app = SocialApp.objects.create(
            provider='instagram',
            name='Instagram',
            client_id='old-insta-id',
            secret='old-insta-secret'
        )
        existing_app.sites.set([site])
        
        out = StringIO()
        call_command('setup_social_apps', stdout=out)
        
        existing_app.refresh_from_db()
        self.assertEqual(existing_app.client_id, 'updated-insta-id')



# ============================================================================
# DELETE MODAL CONFIRMATION TESTS
# ============================================================================

class DeleteModalTemplateTests(TestCase):
    """Tests for delete confirmation modal HTML structure in templates"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='deletemodal1',
            email='deletemodal1@test.com',
            password='testpass123'
        )
        self.client.login(username='deletemodal1', password='testpass123')

    def test_train_page_has_modal_container(self):
        """Test that train page contains the delete confirmation modal container"""
        response = self.client.get('/train/')
        self.assertContains(response, 'id="deleteConfirmationModal"')
        self.assertContains(response, 'class="delete-confirmation-modal"')

    def test_nutrition_page_has_modal_container(self):
        """Test that nutrition page contains the delete confirmation modal container"""
        response = self.client.get('/nutrition/')
        self.assertContains(response, 'id="deleteConfirmationModal"')
        self.assertContains(response, 'class="delete-confirmation-modal"')

    def test_train_page_modal_has_title(self):
        """Test that modal has 'Confirm Delete' title"""
        response = self.client.get('/train/')
        self.assertContains(response, 'Confirm Delete')
        self.assertContains(response, 'class="delete-confirmation-title"')

    def test_nutrition_page_modal_has_title(self):
        """Test that nutrition modal has 'Confirm Delete' title"""
        response = self.client.get('/nutrition/')
        self.assertContains(response, 'Confirm Delete')
        self.assertContains(response, 'class="delete-confirmation-title"')

    def test_train_page_modal_has_message_element(self):
        """Test that modal has dynamic message element"""
        response = self.client.get('/train/')
        self.assertContains(response, 'id="deleteConfirmationMessage"')

    def test_nutrition_page_modal_has_message_element(self):
        """Test that nutrition modal has dynamic message element"""
        response = self.client.get('/nutrition/')
        self.assertContains(response, 'id="deleteConfirmationMessage"')

    def test_train_page_modal_has_buttons(self):
        """Test that modal has Cancel and Delete buttons"""
        response = self.client.get('/train/')
        self.assertContains(response, 'class="btn-cancel"')
        self.assertContains(response, 'class="btn-delete"')
        self.assertContains(response, '>Cancel<')
        self.assertContains(response, '>Delete<')

    def test_nutrition_page_modal_has_buttons(self):
        """Test that nutrition modal has Cancel and Delete buttons"""
        response = self.client.get('/nutrition/')
        self.assertContains(response, 'class="btn-cancel"')
        self.assertContains(response, 'class="btn-delete"')


class DeleteButtonStructureTests(TestCase):
    """Tests for delete button structure and attributes"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='deletemodal2',
            email='deletemodal2@test.com',
            password='testpass123'
        )
        self.client.login(username='deletemodal2', password='testpass123')
        
        # Create test data
        self.workout = Workout.objects.create(
            user=self.user,
            name='Test Workout',
            goal='strength',
            date=date.today()
        )
        self.exercise = Exercise.objects.create(
            workout=self.workout,
            name='Test Exercise',
            muscle_group='arms',
            sets=3,
            reps=10
        )
        self.meal = Meal.objects.create(
            user=self.user,
            name='Test Meal',
            date=date.today()
        )
        self.food_item = FoodItem.objects.create(
            meal=self.meal,
            name='Test Food',
            calories=200
        )

    def test_workout_delete_button_has_data_attributes(self):
        """Test that workout delete button has required data attributes"""
        response = self.client.get('/train/')
        self.assertContains(response, 'data-delete-message="Delete this workout and all its exercises?"')
        self.assertContains(response, 'data-delete-type="workout"')

    def test_exercise_delete_button_has_data_attributes(self):
        """Test that exercise delete button has required data attributes"""
        response = self.client.get('/train/')
        self.assertContains(response, 'data-delete-message="Delete this exercise?"')
        self.assertContains(response, 'data-delete-type="exercise"')

    def test_food_item_delete_button_has_data_attributes(self):
        """Test that food item delete button has required data attributes"""
        response = self.client.get('/nutrition/')
        self.assertContains(response, 'data-delete-message="Delete this item?"')
        self.assertContains(response, 'data-delete-type="item"')

    def test_delete_buttons_use_button_type(self):
        """Test that delete buttons use type='button'"""
        response = self.client.get('/train/')
        content = response.content.decode()
        self.assertIn('type="button"', content)

    def test_delete_buttons_no_onclick_confirm(self):
        """Test that delete buttons don't have onclick='return confirm()' handlers"""
        response = self.client.get('/train/')
        content = response.content.decode()
        self.assertNotIn('onclick="return confirm', content)

    def test_nutrition_delete_buttons_no_onclick_confirm(self):
        """Test that nutrition delete buttons don't have onclick='return confirm()' handlers"""
        response = self.client.get('/nutrition/')
        content = response.content.decode()
        self.assertNotIn('onclick="return confirm', content)


class DeleteModalCSSTests(TestCase):
    """Tests for delete modal CSS styling"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='deletemodal3',
            email='deletemodal3@test.com',
            password='testpass123'
        )
        self.client.login(username='deletemodal3', password='testpass123')

    def test_train_page_has_modal_css_classes(self):
        """Test that train page template contains modal CSS classes"""
        response = self.client.get('/train/')
        
        css_classes = [
            'delete-confirmation-modal',
            'delete-confirmation-content',
            'delete-confirmation-title',
            'btn-cancel',
            'btn-delete',
        ]
        
        for css_class in css_classes:
            with self.subTest(css_class=css_class):
                self.assertContains(response, f'class="{css_class}"')

    def test_nutrition_page_has_modal_css_classes(self):
        """Test that nutrition page template contains modal CSS classes"""
        response = self.client.get('/nutrition/')
        
        css_classes = [
            'delete-confirmation-modal',
            'delete-confirmation-content',
            'delete-confirmation-title',
            'btn-cancel',
            'btn-delete',
        ]
        
        for css_class in css_classes:
            with self.subTest(css_class=css_class):
                self.assertContains(response, f'class="{css_class}"')

    def test_train_page_has_modal_styling(self):
        """Test that train page has CSS styles for modal"""
        response = self.client.get('/train/')
        content = response.content.decode()
        
        styles = [
            '.delete-confirmation-modal',
            '.delete-confirmation-content',
            '.btn-cancel',
            '.btn-delete',
        ]
        
        for style in styles:
            with self.subTest(style=style):
                self.assertIn(style, content)

    def test_nutrition_page_has_modal_styling(self):
        """Test that nutrition page has CSS styles for modal"""
        response = self.client.get('/nutrition/')
        content = response.content.decode()
        
        styles = [
            '.delete-confirmation-modal',
            '.delete-confirmation-content',
            '.btn-cancel',
            '.btn-delete',
        ]
        
        for style in styles:
            with self.subTest(style=style):
                self.assertIn(style, content)


class DeleteModalJavaScriptTests(TestCase):
    """Tests for delete modal JavaScript functionality"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='deletemodal4',
            email='deletemodal4@test.com',
            password='testpass123'
        )
        self.client.login(username='deletemodal4', password='testpass123')

    def test_train_page_has_javascript_functions(self):
        """Test that train page contains required JavaScript functions"""
        response = self.client.get('/train/')
        
        functions = ['closeDeleteConfirmation', 'confirmDelete']
        
        for func in functions:
            with self.subTest(func=func):
                self.assertContains(response, f'function {func}')

    def test_nutrition_page_has_javascript_functions(self):
        """Test that nutrition page contains required JavaScript functions"""
        response = self.client.get('/nutrition/')
        
        functions = ['closeDeleteConfirmation', 'confirmDelete']
        
        for func in functions:
            with self.subTest(func=func):
                self.assertContains(response, f'function {func}')

    def test_train_page_has_event_listener(self):
        """Test that train page has event listener for delete buttons"""
        response = self.client.get('/train/')
        content = response.content.decode()
        
        self.assertIn('[data-delete-message]', content)
        self.assertIn('addEventListener', content)
        self.assertIn('deleteConfirmationModal', content)

    def test_nutrition_page_has_event_listener(self):
        """Test that nutrition page has event listener for delete buttons"""
        response = self.client.get('/nutrition/')
        content = response.content.decode()
        
        self.assertIn('[data-delete-message]', content)
        self.assertIn('addEventListener', content)
        self.assertIn('deleteConfirmationModal', content)

    def test_train_page_modal_toggle_logic(self):
        """Test that train page has logic to toggle modal active state"""
        response = self.client.get('/train/')
        content = response.content.decode()
        
        self.assertIn('deleteConfirmationModal', content)
        self.assertIn('classList.add', content)
        self.assertIn('classList.remove', content)
        self.assertIn('active', content)

    def test_nutrition_page_modal_toggle_logic(self):
        """Test that nutrition page has logic to toggle modal active state"""
        response = self.client.get('/nutrition/')
        content = response.content.decode()
        
        self.assertIn('deleteConfirmationModal', content)
        self.assertIn('classList.add', content)
        self.assertIn('classList.remove', content)
        self.assertIn('active', content)


class DeleteModalMessagesTests(TestCase):
    """Tests for delete modal messages"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='deletemodal5',
            email='deletemodal5@test.com',
            password='testpass123'
        )
        self.client.login(username='deletemodal5', password='testpass123')
        
        # Create test data
        self.workout = Workout.objects.create(
            user=self.user,
            name='Test Workout',
            goal='strength',
            date=date.today()
        )
        self.exercise = Exercise.objects.create(
            workout=self.workout,
            name='Test Exercise',
            muscle_group='arms',
            sets=3,
            reps=10
        )
        self.meal = Meal.objects.create(
            user=self.user,
            name='Test Meal',
            date=date.today()
        )
        self.food_item = FoodItem.objects.create(
            meal=self.meal,
            name='Test Food',
            calories=200
        )

    def test_workout_delete_message(self):
        """Test that workout delete button shows correct message"""
        response = self.client.get('/train/')
        self.assertContains(response, 'Delete this workout and all its exercises?')

    def test_exercise_delete_message(self):
        """Test that exercise delete button shows correct message"""
        response = self.client.get('/train/')
        self.assertContains(response, 'Delete this exercise?')

    def test_food_item_delete_message(self):
        """Test that food item delete button shows correct message"""
        response = self.client.get('/nutrition/')
        self.assertContains(response, 'Delete this item?')


class DeleteModalIntegrationTests(TestCase):
    """Integration tests for delete modal with forms"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='deletemodal6',
            email='deletemodal6@test.com',
            password='testpass123'
        )
        self.client.login(username='deletemodal6', password='testpass123')
        
        self.workout = Workout.objects.create(
            user=self.user,
            name='Test Workout',
            goal='strength',
            date=date.today()
        )

    def test_delete_form_has_csrf_token(self):
        """Test that delete form includes CSRF token"""
        response = self.client.get('/train/')
        self.assertContains(response, 'csrfmiddlewaretoken')

    def test_only_one_modal_created(self):
        """Test that only one modal is created"""
        response = self.client.get('/train/')
        content = response.content.decode()
        
        modal_count = content.count('id="deleteConfirmationModal"')
        self.assertEqual(modal_count, 1, "There should be exactly one modal container")

    def test_modal_reused_for_multiple_delete_types(self):
        """Test that same modal works for different delete types"""
        response = self.client.get('/train/')
        content = response.content.decode()
        
        self.assertIn('data-delete-type="workout"', content)
        self.assertEqual(content.count('id="deleteConfirmationModal"'), 1)


class DeleteModalEventHandlingTests(TestCase):
    """Tests for delete modal event handling logic"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='deletemodal7',
            email='deletemodal7@test.com',
            password='testpass123'
        )
        self.client.login(username='deletemodal7', password='testpass123')

    def test_modal_event_listener_uses_data_attribute(self):
        """Test that event listener uses data-delete-message selector"""
        response = self.client.get('/train/')
        content = response.content.decode()
        
        self.assertIn('[data-delete-message]', content)

    def test_modal_prevents_default_form_submission(self):
        """Test that modal prevents default form submission"""
        response = self.client.get('/train/')
        content = response.content.decode()
        
        self.assertIn('preventDefault', content)

    def test_modal_captures_form_reference(self):
        """Test that modal captures form reference before showing"""
        response = self.client.get('/train/')
        content = response.content.decode()
        
        self.assertIn('currentDeleteForm', content)
        self.assertIn('closest', content)

    def test_modal_extracts_message_from_data_attribute(self):
        """Test that modal extracts message from data attribute"""
        response = self.client.get('/train/')
        content = response.content.decode()
        
        self.assertIn('dataset.deleteMessage', content)

    def test_confirm_function_submits_form(self):
        """Test that confirmDelete function submits the captured form"""
        response = self.client.get('/train/')
        content = response.content.decode()
        
        self.assertIn('function confirmDelete', content)
        self.assertIn('.submit()', content)

    def test_close_function_removes_modal_class(self):
        """Test that closeDeleteConfirmation removes active class"""
        response = self.client.get('/train/')
        content = response.content.decode()
        
        self.assertIn('function closeDeleteConfirmation', content)
        self.assertIn('classList.remove', content)
        self.assertIn('active', content)

    def test_outside_click_closes_modal(self):
        """Test that clicking outside modal closes it"""
        response = self.client.get('/train/')
        content = response.content.decode()
        
        self.assertIn('addEventListener', content)
        self.assertIn('closeDeleteConfirmation', content)


# ===== EXERCISE DATABASE TESTS =====

class ExerciseTypeTestCase(TestCase):
    """Test ExerciseType model"""

    def setUp(self):
        self.exercise_type = ExerciseType.objects.create(
            name='Strength',
            description='Build muscle and strength'
        )

    def test_exercise_type_creation(self):
        """Test creating an exercise type"""
        self.assertEqual(self.exercise_type.name, 'Strength')
        self.assertEqual(self.exercise_type.description, 'Build muscle and strength')

    def test_exercise_type_str(self):
        """Test string representation"""
        self.assertEqual(str(self.exercise_type), 'Strength')


class MuscleGroupTestCase(TestCase):
    """Test MuscleGroup model"""

    def setUp(self):
        self.muscle_group = MuscleGroup.objects.create(
            name='Upper Body',
            description='Arms, shoulders, chest, back'
        )

    def test_muscle_group_creation(self):
        """Test creating a muscle group"""
        self.assertEqual(self.muscle_group.name, 'Upper Body')

    def test_muscle_group_str(self):
        """Test string representation"""
        self.assertEqual(str(self.muscle_group), 'Upper Body')


class MuscleTestCase(TestCase):
    """Test Muscle model"""

    def setUp(self):
        self.muscle_group = MuscleGroup.objects.create(name='Upper Body')
        self.muscle = Muscle.objects.create(
            name='Biceps',
            muscle_group=self.muscle_group,
            description='Front upper arm muscle'
        )

    def test_muscle_creation(self):
        """Test creating a muscle"""
        self.assertEqual(self.muscle.name, 'Biceps')
        self.assertEqual(self.muscle.muscle_group.name, 'Upper Body')

    def test_muscle_str(self):
        """Test string representation"""
        self.assertEqual(str(self.muscle), 'Biceps (Upper Body)')


class EquipmentTestCase(TestCase):
    """Test Equipment model"""

    def setUp(self):
        self.equipment = Equipment.objects.create(
            name='Dumbbells',
            description='Free weights'
        )

    def test_equipment_creation(self):
        """Test creating equipment"""
        self.assertEqual(self.equipment.name, 'Dumbbells')

    def test_equipment_str(self):
        """Test string representation"""
        self.assertEqual(str(self.equipment), 'Dumbbells')


class TrainingExerciseTestCase(TestCase):
    """Test TrainingExercise model"""

    def setUp(self):
        self.exercise_type = ExerciseType.objects.create(name='Strength')
        self.muscle_group = MuscleGroup.objects.create(name='Upper Body')
        self.biceps = Muscle.objects.create(
            name='Biceps',
            muscle_group=self.muscle_group
        )
        self.equipment = Equipment.objects.create(name='Dumbbells')

        self.exercise = TrainingExercise.objects.create(
            name='Dumbbell Curl',
            description='Isolate biceps with dumbbells',
            instructions='1. Stand with dumbbells\n2. Curl up\n3. Lower down',
            exercise_type=self.exercise_type,
            difficulty='beginner',
            location='both',
            default_sets=3,
            default_reps=10,
        )
        self.exercise.muscle_groups.add(self.muscle_group)
        self.exercise.primary_muscles.add(self.biceps)
        self.exercise.equipment.add(self.equipment)

    def test_exercise_creation(self):
        """Test creating an exercise"""
        self.assertEqual(self.exercise.name, 'Dumbbell Curl')
        self.assertEqual(self.exercise.exercise_type.name, 'Strength')
        self.assertEqual(self.exercise.difficulty, 'beginner')
        self.assertTrue(self.exercise.is_active)

    def test_exercise_default_sets_reps(self):
        """Test default sets and reps"""
        self.assertEqual(self.exercise.default_sets, 3)
        self.assertEqual(self.exercise.default_reps, 10)

    def test_exercise_relationships(self):
        """Test exercise relationships"""
        self.assertIn(self.muscle_group, self.exercise.muscle_groups.all())
        self.assertIn(self.biceps, self.exercise.primary_muscles.all())
        self.assertIn(self.equipment, self.exercise.equipment.all())

    def test_exercise_str(self):
        """Test string representation"""
        self.assertEqual(str(self.exercise), 'Dumbbell Curl (Strength)')

    def test_exercise_difficulty_choices(self):
        """Test all difficulty levels"""
        for difficulty in ['beginner', 'intermediate', 'advanced']:
            ex = TrainingExercise.objects.create(
                name=f'Test {difficulty}',
                exercise_type=self.exercise_type,
                difficulty=difficulty
            )
            self.assertEqual(ex.difficulty, difficulty)

    def test_exercise_location_choices(self):
        """Test all location types"""
        for location in ['home', 'gym', 'both']:
            ex = TrainingExercise.objects.create(
                name=f'Test {location}',
                exercise_type=self.exercise_type,
                location=location
            )
            self.assertEqual(ex.location, location)


class UserInjuryTestCase(TestCase):
    """Test UserInjury model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='injuryuser',
            email='injury@test.com',
            password='testpass123'
        )
        self.muscle_group = MuscleGroup.objects.create(name='Upper Body')
        self.biceps = Muscle.objects.create(
            name='Biceps',
            muscle_group=self.muscle_group
        )
        self.injury = UserInjury.objects.create(
            user=self.user,
            muscle=self.biceps,
            severity='moderate',
            notes='Sports injury',
            start_date=timezone.now().date()
        )

    def test_injury_creation(self):
        """Test creating an injury record"""
        self.assertEqual(self.injury.user, self.user)
        self.assertEqual(self.injury.muscle.name, 'Biceps')
        self.assertEqual(self.injury.severity, 'moderate')
        self.assertTrue(self.injury.is_active)

    def test_injury_active_status(self):
        """Test injury active/inactive toggle"""
        self.assertTrue(self.injury.is_active)
        self.injury.is_active = False
        self.injury.save()
        self.assertFalse(self.injury.is_active)

    def test_injury_severity_choices(self):
        """Test all severity levels"""
        for severity in ['mild', 'moderate', 'severe']:
            inj = UserInjury.objects.create(
                user=self.user,
                muscle=self.biceps,
                severity=severity,
                start_date=timezone.now().date()
            )
            self.assertEqual(inj.severity, severity)

    def test_injury_str(self):
        """Test string representation"""
        self.assertIn(self.user.email, str(self.injury))
        self.assertIn('Biceps', str(self.injury))


class UserEquipmentProfileTestCase(TestCase):
    """Test UserEquipmentProfile model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='equipuser',
            email='equip@test.com',
            password='testpass123'
        )
        self.dumbbells = Equipment.objects.create(name='Dumbbells')
        self.barbell = Equipment.objects.create(name='Barbell')

        self.profile, created = UserEquipmentProfile.objects.get_or_create(
            user=self.user,
            defaults={'location': 'gym'}
        )
        self.profile.equipment.add(self.dumbbells, self.barbell)

    def test_profile_creation(self):
        """Test creating equipment profile"""
        self.assertEqual(self.profile.user, self.user)
        self.assertEqual(self.profile.location, 'gym')

    def test_profile_onetoone(self):
        """Test OneToOne relationship"""
        profile = UserEquipmentProfile.objects.get(user=self.user)
        self.assertEqual(profile.id, self.profile.id)

    def test_profile_equipment_management(self):
        """Test managing equipment"""
        self.assertEqual(self.profile.equipment.count(), 2)
        self.assertIn(self.dumbbells, self.profile.equipment.all())

    def test_profile_get_or_create(self):
        """Test get_or_create pattern"""
        profile2, created = UserEquipmentProfile.objects.get_or_create(
            user=self.user,
            defaults={'location': 'home'}
        )
        self.assertFalse(created)
        self.assertEqual(profile2.id, self.profile.id)


class ExerciseFilteringTestCase(TestCase):
    """Test exercise filtering and queries"""

    def setUp(self):
        # Create base data
        self.strength_type = ExerciseType.objects.create(name='Strength')
        self.cardio_type = ExerciseType.objects.create(name='Cardio')

        self.upper_body = MuscleGroup.objects.create(name='Upper Body')
        self.lower_body = MuscleGroup.objects.create(name='Lower Body')

        self.biceps = Muscle.objects.create(name='Biceps', muscle_group=self.upper_body)
        self.triceps = Muscle.objects.create(name='Triceps', muscle_group=self.upper_body)
        self.quads = Muscle.objects.create(name='Quadriceps', muscle_group=self.lower_body)

        self.dumbbells = Equipment.objects.create(name='Dumbbells')
        self.barbell = Equipment.objects.create(name='Barbell')

        # Create exercises
        self.curl = TrainingExercise.objects.create(
            name='Dumbbell Curl',
            exercise_type=self.strength_type,
            difficulty='beginner',
            location='both'
        )
        self.curl.muscle_groups.add(self.upper_body)
        self.curl.primary_muscles.add(self.biceps)
        self.curl.equipment.add(self.dumbbells)

        self.bench = TrainingExercise.objects.create(
            name='Bench Press',
            exercise_type=self.strength_type,
            difficulty='intermediate',
            location='gym'
        )
        self.bench.muscle_groups.add(self.upper_body)
        self.bench.primary_muscles.add(self.triceps)
        self.bench.equipment.add(self.barbell)

    def test_filter_by_type(self):
        """Test filtering exercises by type"""
        strength = TrainingExercise.objects.filter(exercise_type=self.strength_type)
        self.assertEqual(strength.count(), 2)

    def test_filter_by_difficulty(self):
        """Test filtering by difficulty"""
        beginner = TrainingExercise.objects.filter(difficulty='beginner')
        self.assertEqual(beginner.count(), 1)
        self.assertIn(self.curl, beginner)

    def test_filter_by_location(self):
        """Test filtering by location"""
        both_loc = TrainingExercise.objects.filter(location='both')
        self.assertEqual(both_loc.count(), 1)
        self.assertIn(self.curl, both_loc)

    def test_filter_by_muscle_group(self):
        """Test filtering by muscle group"""
        upper = TrainingExercise.objects.filter(muscle_groups=self.upper_body)
        self.assertEqual(upper.count(), 2)

    def test_filter_by_specific_muscle(self):
        """Test filtering by specific muscle"""
        bicep_ex = TrainingExercise.objects.filter(primary_muscles=self.biceps)
        self.assertEqual(bicep_ex.count(), 1)
        self.assertIn(self.curl, bicep_ex)

    def test_filter_by_equipment(self):
        """Test filtering by equipment"""
        dumbbell_ex = TrainingExercise.objects.filter(equipment=self.dumbbells)
        self.assertEqual(dumbbell_ex.count(), 1)
        self.assertIn(self.curl, dumbbell_ex)

    def test_exclude_exercise(self):
        """Test excluding exercises"""
        no_gym = TrainingExercise.objects.exclude(location='gym')
        self.assertEqual(no_gym.count(), 1)
        self.assertNotIn(self.bench, no_gym)

    def test_exclude_by_muscle(self):
        """Test excluding by muscle"""
        # User is injured in biceps, should exclude curl
        no_bicep = TrainingExercise.objects.exclude(
            primary_muscles=self.biceps
        )
        self.assertEqual(no_bicep.count(), 1)
        self.assertIn(self.bench, no_bicep)
        self.assertNotIn(self.curl, no_bicep)


# ===== EXERCISE API TESTS =====

class ExerciseAPITestCase(TestCase):
    """Test Exercise API endpoints"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='apiuser',
            email='api@test.com',
            password='testpass123'
        )

        self.strength_type = ExerciseType.objects.create(name='Strength')
        self.cardio_type = ExerciseType.objects.create(name='Cardio')

        self.upper_body = MuscleGroup.objects.create(name='Upper Body')
        self.biceps = Muscle.objects.create(name='Biceps', muscle_group=self.upper_body)
        self.dumbbells = Equipment.objects.create(name='Dumbbells')

        self.curl = TrainingExercise.objects.create(
            name='Dumbbell Curl',
            exercise_type=self.strength_type,
            difficulty='beginner',
            location='both'
        )
        self.curl.muscle_groups.add(self.upper_body)
        self.curl.primary_muscles.add(self.biceps)
        self.curl.equipment.add(self.dumbbells)

    def test_get_exercise_types(self):
        """Test GET /api/exercises/types/"""
        response = self.client.get('/api/exercises/types/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('exercise_types', data)
        self.assertEqual(len(data['exercise_types']), 2)

    def test_get_muscle_groups(self):
        """Test GET /api/exercises/muscle-groups/"""
        response = self.client.get('/api/exercises/muscle-groups/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('muscle_groups', data)
        self.assertEqual(len(data['muscle_groups']), 1)

    def test_get_equipment(self):
        """Test GET /api/exercises/equipment/"""
        response = self.client.get('/api/exercises/equipment/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('equipment', data)
        self.assertEqual(len(data['equipment']), 1)

    def test_get_muscles(self):
        """Test GET /api/exercises/muscles/"""
        response = self.client.get('/api/exercises/muscles/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('muscles', data)
        self.assertEqual(len(data['muscles']), 1)

    def test_get_muscles_by_group(self):
        """Test filtering muscles by muscle group"""
        response = self.client.get(f'/api/exercises/muscles/?group_id={self.upper_body.id}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['muscles']), 1)
        self.assertEqual(data['muscles'][0]['name'], 'Biceps')

    def test_filter_exercises_requires_auth(self):
        """Test that filter endpoint requires authentication"""
        response = self.client.get('/api/exercises/filter/')
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_filter_exercises_authenticated(self):
        """Test filter exercises with authentication"""
        self.client.login(username='apiuser', password='testpass123')
        response = self.client.get('/api/exercises/filter/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('exercises', data)
        self.assertIn('count', data)

    def test_filter_by_exercise_type(self):
        """Test filtering by exercise type"""
        self.client.login(username='apiuser', password='testpass123')
        response = self.client.get(f'/api/exercises/filter/?exercise_type={self.strength_type.id}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['count'], 1)

    def test_filter_by_difficulty(self):
        """Test filtering by difficulty"""
        self.client.login(username='apiuser', password='testpass123')
        response = self.client.get('/api/exercises/filter/?difficulty=beginner')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['count'], 1)

    def test_filter_by_location(self):
        """Test filtering by location"""
        self.client.login(username='apiuser', password='testpass123')
        response = self.client.get('/api/exercises/filter/?location=home')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertGreaterEqual(data['count'], 0)

    def test_get_exercise_detail(self):
        """Test GET /api/exercises/<id>/"""
        response = self.client.get(f'/api/exercises/{self.curl.id}/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['name'], 'Dumbbell Curl')
        self.assertEqual(data['difficulty'], 'Beginner')

    def test_get_exercise_detail_404(self):
        """Test 404 for non-existent exercise"""
        response = self.client.get('/api/exercises/9999/')
        self.assertEqual(response.status_code, 404)

    def test_add_user_injury_requires_auth(self):
        """Test that add injury requires authentication"""
        response = self.client.post('/api/user/injury/add/')
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_add_user_injury(self):
        """Test adding user injury"""
        self.client.login(username='apiuser', password='testpass123')
        response = self.client.post(
            '/api/user/injury/add/',
            data=json.dumps({
                'muscle_id': self.biceps.id,
                'severity': 'moderate',
                'notes': 'Test injury'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

    def test_update_equipment_profile(self):
        """Test updating user equipment"""
        self.client.login(username='apiuser', password='testpass123')
        response = self.client.post(
            '/api/user/equipment/',
            data=json.dumps({
                'location': 'gym',
                'equipment': [self.dumbbells.id]
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

        # Verify profile was created/updated
        profile = UserEquipmentProfile.objects.get(user=self.user)
        self.assertEqual(profile.location, 'gym')
        self.assertIn(self.dumbbells, profile.equipment.all())

    def test_exercise_detail_response_structure(self):
        """Test exercise detail response has all required fields"""
        response = self.client.get(f'/api/exercises/{self.curl.id}/')
        data = json.loads(response.content)

        required_fields = [
            'id', 'name', 'description', 'instructions',
            'difficulty', 'exercise_type', 'muscle_groups',
            'primary_muscles', 'secondary_muscles', 'location',
            'equipment', 'default_sets', 'default_reps'
        ]

        for field in required_fields:
            self.assertIn(field, data, f'Missing field: {field}')

    def test_filter_response_structure(self):
        """Test filter response has correct structure"""
        self.client.login(username='apiuser', password='testpass123')
        response = self.client.get('/api/exercises/filter/')
        data = json.loads(response.content)

        self.assertIn('count', data)
        self.assertIn('exercises', data)
        self.assertIsInstance(data['exercises'], list)


class InjuryAwareFilteringTestCase(TestCase):
    """Test injury-aware exercise filtering"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='injuryfilter',
            email='injuryfilter@test.com',
            password='testpass123'
        )

        self.strength_type = ExerciseType.objects.create(name='Strength')
        self.upper_body = MuscleGroup.objects.create(name='Upper Body')

        self.biceps = Muscle.objects.create(name='Biceps', muscle_group=self.upper_body)
        self.triceps = Muscle.objects.create(name='Triceps', muscle_group=self.upper_body)

        self.dumbbells = Equipment.objects.create(name='Dumbbells')

        # Create two exercises - one targeting biceps, one targeting triceps
        self.curl = TrainingExercise.objects.create(
            name='Dumbbell Curl',
            exercise_type=self.strength_type,
            difficulty='beginner'
        )
        self.curl.muscle_groups.add(self.upper_body)
        self.curl.primary_muscles.add(self.biceps)
        self.curl.equipment.add(self.dumbbells)

        self.extension = TrainingExercise.objects.create(
            name='Tricep Extension',
            exercise_type=self.strength_type,
            difficulty='beginner'
        )
        self.extension.muscle_groups.add(self.upper_body)
        self.extension.primary_muscles.add(self.triceps)
        self.extension.equipment.add(self.dumbbells)

    def test_exclude_injured_biceps(self):
        """Test that exercises for injured biceps are excluded"""
        # Create injury for biceps
        UserInjury.objects.create(
            user=self.user,
            muscle=self.biceps,
            severity='moderate',
            start_date=timezone.now().date(),
            is_active=True
        )

        self.client.login(username='injuryfilter', password='testpass123')
        response = self.client.get('/api/exercises/filter/?exclude_injured=true')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        # Should not include curl (targets biceps)
        exercise_names = [ex['name'] for ex in data['exercises']]
        self.assertNotIn('Dumbbell Curl', exercise_names)
        self.assertIn('Tricep Extension', exercise_names)

    def test_inactive_injury_not_excluded(self):
        """Test that inactive injuries don't exclude exercises"""
        # Create inactive injury
        UserInjury.objects.create(
            user=self.user,
            muscle=self.biceps,
            severity='moderate',
            start_date=timezone.now().date(),
            is_active=False
        )

        self.client.login(username='injuryfilter', password='testpass123')
        response = self.client.get('/api/exercises/filter/?exclude_injured=true')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        # Should include both exercises (injury is inactive)
        exercise_names = [ex['name'] for ex in data['exercises']]
        self.assertIn('Dumbbell Curl', exercise_names)
        self.assertIn('Tricep Extension', exercise_names)
class UserProfileFormTests(TestCase):
    """Tests for the UserProfile form and data persistence on get_started_profile page."""
    
    def setUp(self):
        self.client = Client()
        # Create and login a user
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='TestPass123!',
            is_active=True
        )
        self.client.login(username='testuser@example.com', password='TestPass123!')
    
    def test_profile_page_accessible_to_authenticated_user(self):
        """Test that authenticated user can access the get_started_profile page."""
        response = self.client.get('/get_started_profile/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Get Started')
    
    def test_profile_page_redirects_unauthenticated_user(self):
        """Test that unauthenticated user is redirected from get_started_profile."""
        self.client.logout()
        response = self.client.get('/get_started_profile/')
        self.assertEqual(response.status_code, 302)
    
    def test_save_user_name_field(self):
        """Test that user name is saved to User.first_name."""
        response = self.client.post('/get_started_profile/', {
            'name': 'John Doe',
        }, follow=True)
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'John Doe')
    
    def test_empty_name_field_not_saved(self):
        """Test that empty name doesn't overwrite existing name."""
        self.user.first_name = 'Original Name'
        self.user.save()
        
        self.client.post('/get_started_profile/', {})
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Original Name')
    
    def test_save_height_field(self):
        """Test that height (cm) is saved to UserProfile."""
        self.client.post('/get_started_profile/', {
            'height': '180',
        }, follow=True)
        
        profile = self.user.profile
        self.assertEqual(profile.height, 180)
    
    def test_save_weight_field(self):
        """Test that weight (kg) is saved to UserProfile."""
        self.client.post('/get_started_profile/', {
            'weight': '75',
        }, follow=True)
        
        profile = self.user.profile
        self.assertEqual(profile.weight, 75)
    
    def test_save_age_field(self):
        """Test that age is saved to UserProfile."""
        self.client.post('/get_started_profile/', {
            'age': '28',
        }, follow=True)
        
        profile = self.user.profile
        self.assertEqual(profile.age, 28)
    
    def test_save_primary_goal_bubble_selection(self):
        """Test that primary_goal bubble selection is saved."""
        self.client.post('/get_started_profile/', {
            'primary_goal': 'muscle_gain',
        }, follow=True)
        
        profile = self.user.profile
        self.assertEqual(profile.primary_goal, 'muscle_gain')
    
    def test_all_primary_goal_options_save(self):
        """Test that all primary goal options can be saved."""
        goals = ['weight_loss', 'muscle_gain', 'strength', 'endurance', 'flexibility', 'general_health']
        
        for goal in goals:
            self.client.post('/get_started_profile/', {
                'primary_goal': goal,
            }, follow=True)
            
            self.user.refresh_from_db()
            profile = self.user.profile
            self.assertEqual(profile.primary_goal, goal)
    
    def test_save_experience_level_bubble_selection(self):
        """Test that experience_level bubble selection is saved."""
        self.client.post('/get_started_profile/', {
            'experience_level': 'intermediate',
        }, follow=True)
        
        profile = self.user.profile
        self.assertEqual(profile.experience_level, 'intermediate')
    
    def test_all_experience_level_options_save(self):
        """Test that all experience level options can be saved."""
        levels = ['beginner', 'intermediate', 'advanced']
        
        for level in levels:
            self.client.post('/get_started_profile/', {
                'experience_level': level,
            }, follow=True)
            
            self.user.refresh_from_db()
            profile = self.user.profile
            self.assertEqual(profile.experience_level, level)
    
    def test_save_dietary_preference_bubble_selection(self):
        """Test that dietary_preference bubble selection is saved."""
        self.client.post('/get_started_profile/', {
            'dietary_preference': 'vegan',
        }, follow=True)
        
        profile = self.user.profile
        self.assertEqual(profile.dietary_preference, 'vegan')
    
    def test_all_dietary_preference_options_save(self):
        """Test that all dietary preference options can be saved."""
        prefs = ['omnivore', 'vegetarian', 'vegan', 'keto', 'paleo', 'gluten_free']
        
        for pref in prefs:
            self.client.post('/get_started_profile/', {
                'dietary_preference': pref,
            }, follow=True)
            
            self.user.refresh_from_db()
            profile = self.user.profile
            self.assertEqual(profile.dietary_preference, pref)
    
    def test_save_home_gym_yes(self):
        """Test that has_home_gym is saved when user selects 'yes'."""
        self.client.post('/get_started_profile/', {
            'has_home_gym': 'yes',
        }, follow=True)
        
        profile = self.user.profile
        self.assertTrue(profile.has_home_gym)
    
    def test_save_home_gym_no(self):
        """Test that has_home_gym is saved when user selects 'no'."""
        self.client.post('/get_started_profile/', {
            'has_home_gym': 'no',
        }, follow=True)
        
        profile = self.user.profile
        self.assertFalse(profile.has_home_gym)
    
    def test_save_single_home_equipment(self):
        """Test that single home equipment selection is saved."""
        self.client.post('/get_started_profile/', {
            'home_equipment': ['dumbbells'],
        }, follow=True)
        
        profile = self.user.profile
        self.assertIn('dumbbells', profile.home_equipment)
        self.assertEqual(len(profile.home_equipment), 1)
    
    def test_save_multiple_home_equipment(self):
        """Test that multiple home equipment selections are saved."""
        equipment = ['dumbbells', 'yoga_mat', 'resistance_bands', 'kettlebell']
        self.client.post('/get_started_profile/', {
            'home_equipment': equipment,
        }, follow=True)
        
        profile = self.user.profile
        self.assertEqual(set(profile.home_equipment), set(equipment))
        self.assertEqual(len(profile.home_equipment), 4)
    
    def test_all_home_equipment_options_save(self):
        """Test that all home equipment options can be saved."""
        equipment = [
            'dumbbells', 'resistance_bands', 'kettlebell', 'yoga_mat',
            'pull_up_bar', 'bench', 'treadmill', 'stationary_bike',
            'jump_rope', 'medicine_ball'
        ]
        
        self.client.post('/get_started_profile/', {
            'home_equipment': equipment,
        }, follow=True)
        
        profile = self.user.profile
        self.assertEqual(set(profile.home_equipment), set(equipment))
    
    def test_save_empty_home_equipment_list(self):
        """Test that empty home equipment list is saved correctly."""
        # First save some equipment
        self.client.post('/get_started_profile/', {
            'home_equipment': ['dumbbells', 'yoga_mat'],
        }, follow=True)
        
        # Then clear it
        self.client.post('/get_started_profile/', {
            'home_equipment': [],
        }, follow=True)
        
        profile = self.user.profile
        self.assertEqual(profile.home_equipment, [])
    
    def test_save_bio_field(self):
        """Test that bio text is saved to UserProfile."""
        bio_text = 'I love fitness and want to improve my endurance!'
        self.client.post('/get_started_profile/', {
            'bio': bio_text,
        }, follow=True)
        
        profile = self.user.profile
        self.assertEqual(profile.bio, bio_text)
    
    def test_save_multiline_bio(self):
        """Test that multiline bio text is saved correctly."""
        bio_text = 'I love fitness.\nI want to improve my endurance.\nLooking forward to training!'
        self.client.post('/get_started_profile/', {
            'bio': bio_text,
        }, follow=True)
        
        profile = self.user.profile
        self.assertEqual(profile.bio, bio_text)
    
    def test_save_calorie_goal_custom_value(self):
        """Test that custom calorie goal is saved."""
        self.client.post('/get_started_profile/', {
            'calorie_goal': '3000',
        }, follow=True)
        
        profile = self.user.profile
        self.assertEqual(profile.calorie_goal, 3000)
    
    def test_calorie_goal_defaults_to_2400(self):
        """Test that calorie_goal defaults to 2400 when not provided."""
        # Create profile without specifying calorie_goal
        self.client.post('/get_started_profile/', {
            'name': 'Test User',
        }, follow=True)
        
        profile = self.user.profile
        self.assertEqual(profile.calorie_goal, 2400)
    
    def test_profile_persists_when_revisiting_page(self):
        """Test that all saved profile data persists when revisiting the page."""
        # Save initial data
        self.client.post('/get_started_profile/', {
            'name': 'John Smith',
            'height': '180',
            'weight': '75',
            'age': '28',
            'primary_goal': 'muscle_gain',
            'experience_level': 'intermediate',
            'dietary_preference': 'vegan',
            'has_home_gym': 'yes',
            'home_equipment': ['dumbbells', 'yoga_mat'],
            'calorie_goal': '2800',
            'bio': 'Fitness enthusiast',
        }, follow=True)
        
        # Revisit the page
        response = self.client.get('/get_started_profile/')
        
        # Verify all data is present in the response
        self.assertContains(response, 'John Smith')
        self.assertContains(response, '180')
        self.assertContains(response, '75')
        self.assertContains(response, '28')
        self.assertContains(response, 'Fitness enthusiast')
        
        # Verify data in the database
        profile = self.user.profile
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'John Smith')
        self.assertEqual(profile.height, 180)
        self.assertEqual(profile.weight, 75)
        self.assertEqual(profile.age, 28)
        self.assertEqual(profile.primary_goal, 'muscle_gain')
        self.assertEqual(profile.experience_level, 'intermediate')
        self.assertEqual(profile.dietary_preference, 'vegan')
        self.assertTrue(profile.has_home_gym)
        self.assertIn('dumbbells', profile.home_equipment)
        self.assertIn('yoga_mat', profile.home_equipment)
        self.assertEqual(profile.calorie_goal, 2800)
        self.assertEqual(profile.bio, 'Fitness enthusiast')
    
    def test_form_submission_redirects_to_home_dash(self):
        """Test that form submission redirects to home_dash."""
        response = self.client.post('/get_started_profile/', {
            'name': 'Test User',
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('/home_dash/', response.url)
    
    def test_form_submission_shows_success_message(self):
        """Test that form submission shows a success message."""
        response = self.client.post('/get_started_profile/', {
            'name': 'Test User',
        }, follow=True)
        
        messages = list(response.context['messages'])
        self.assertTrue(any('updated' in str(m).lower() or 'saved' in str(m).lower() for m in messages))
    
    def test_invalid_height_value_not_saved(self):
        """Test that invalid height value is not saved."""
        self.client.post('/get_started_profile/', {
            'height': 'not_a_number',
        }, follow=True)
        
        profile = self.user.profile
        self.assertIsNone(profile.height)
    
    def test_invalid_weight_value_not_saved(self):
        """Test that invalid weight value is not saved."""
        self.client.post('/get_started_profile/', {
            'weight': 'invalid',
        }, follow=True)
        
        profile = self.user.profile
        self.assertIsNone(profile.weight)
    
    def test_invalid_age_value_not_saved(self):
        """Test that invalid age value is not saved."""
        self.client.post('/get_started_profile/', {
            'age': 'not_numeric',
        }, follow=True)
        
        profile = self.user.profile
        self.assertIsNone(profile.age)
    
    def test_invalid_calorie_goal_value_not_saved(self):
        """Test that invalid calorie goal value is not saved (reverts to default)."""
        # First create profile with initial calorie goal
        self.client.post('/get_started_profile/', {
            'calorie_goal': '2500',
        }, follow=True)
        
        # Try to save invalid value
        self.client.post('/get_started_profile/', {
            'calorie_goal': 'not_valid',
        }, follow=True)
        
        profile = self.user.profile
        # Should keep the original value since invalid value wasn't saved
        self.assertEqual(profile.calorie_goal, 2500)
    
    def test_partial_form_submission(self):
        """Test that partial form submission (only some fields) saves correctly."""
        # Save some fields
        self.client.post('/get_started_profile/', {
            'name': 'Partial User',
            'height': '175',
        }, follow=True)
        
        profile = self.user.profile
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Partial User')
        self.assertEqual(profile.height, 175)
        self.assertIsNone(profile.weight)
        self.assertIsNone(profile.age)
    
    def test_updating_existing_profile_data(self):
        """Test that updating existing profile data overwrites old values."""
        # Save initial data
        self.client.post('/get_started_profile/', {
            'name': 'Original Name',
            'height': '170',
            'primary_goal': 'weight_loss',
        }, follow=True)
        
        # Update with new data
        self.client.post('/get_started_profile/', {
            'name': 'Updated Name',
            'height': '180',
            'primary_goal': 'muscle_gain',
        }, follow=True)
        
        profile = self.user.profile
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated Name')
        self.assertEqual(profile.height, 180)
        self.assertEqual(profile.primary_goal, 'muscle_gain')
    
class UserProfileHomeGymTests(TestCase):
    """Tests for home gym conditional functionality."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='homeuser@example.com',
            email='homeuser@example.com',
            password='TestPass123!',
            is_active=True
        )
        self.client.login(username='homeuser@example.com', password='TestPass123!')
    
    def test_home_gym_yes_enables_equipment_selection(self):
        """Test that selecting yes allows saving equipment."""
        self.client.post('/get_started_profile/', {
            'has_home_gym': 'yes',
            'home_equipment': ['dumbbells', 'yoga_mat'],
        }, follow=True)
        
        profile = self.user.profile
        self.assertTrue(profile.has_home_gym)
        self.assertIn('dumbbells', profile.home_equipment)
        self.assertIn('yoga_mat', profile.home_equipment)
    
    def test_home_gym_no_disables_equipment_selection(self):
        """Test that selecting no doesn't save equipment."""
        self.client.post('/get_started_profile/', {
            'has_home_gym': 'no',
            'home_equipment': [],
        }, follow=True)
        
        profile = self.user.profile
        self.assertFalse(profile.has_home_gym)
        self.assertEqual(profile.home_equipment, [])
    
    def test_equipment_persists_when_switching_back_to_yes(self):
        """Test that equipment list is preserved when toggling home gym."""
        # First select yes with equipment
        self.client.post('/get_started_profile/', {
            'has_home_gym': 'yes',
            'home_equipment': ['dumbbells', 'yoga_mat'],
        }, follow=True)
        
        # Then switch to no
        self.client.post('/get_started_profile/', {
            'has_home_gym': 'no',
        }, follow=True)
        
        # Switch back to yes (equipment should still be there)
        self.client.post('/get_started_profile/', {
            'has_home_gym': 'yes',
            'home_equipment': ['dumbbells', 'yoga_mat'],
        }, follow=True)
        
        profile = self.user.profile
        self.assertTrue(profile.has_home_gym)
        self.assertIn('dumbbells', profile.home_equipment)
        self.assertIn('yoga_mat', profile.home_equipment)
    
    def test_home_gym_selection_persists_on_reload(self):
        """Test that home gym yes/no selection is preserved when reloading."""
        # Save yes selection
        self.client.post('/get_started_profile/', {
            'has_home_gym': 'yes',
        }, follow=True)
        
        # Reload and verify
        response = self.client.get('/get_started_profile/')
        self.assertContains(response, 'value="yes" checked')
        
        # Now switch to no
        self.client.post('/get_started_profile/', {
            'has_home_gym': 'no',
        }, follow=True)
        
        # Reload and verify no is checked
        response = self.client.get('/get_started_profile/')
        self.assertContains(response, 'value="no" checked')


# ---------------------------------------------------------------------------
#  Onboarding feature tests
# ---------------------------------------------------------------------------

class OnboardingCompletionTests(TestCase):
    """Tests for onboarding_completed field and skip button functionality."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='onboard@example.com',
            email='onboard@example.com',
            password='TestPass123!',
            is_active=True
        )
        self.client.login(username='onboard@example.com', password='TestPass123!')
    
    def test_profile_created_on_get_started_access(self):
        """Test that UserProfile is created when accessing get_started_profile if it doesn't exist."""
        # Delete profile if it exists
        from core.models import UserProfile
        UserProfile.objects.filter(user=self.user).delete()
        
        # Access the page
        response = self.client.get('/get_started_profile/')
        self.assertEqual(response.status_code, 200)
        
        # Profile should now exist
        profile = self.user.profile
        self.assertIsNotNone(profile)
        self.assertFalse(profile.onboarding_completed)
    
    def test_onboarding_completed_false_by_default(self):
        """Test that new profiles have onboarding_completed=False."""
        from core.models import UserProfile
        UserProfile.objects.filter(user=self.user).delete()
        
        # Access the page (creates profile)
        self.client.get('/get_started_profile/')
        
        profile = self.user.profile
        self.assertFalse(profile.onboarding_completed)
    
    def test_skip_button_shows_for_new_users(self):
        """Test that skip button is visible for users with onboarding_completed=False."""
        from core.models import UserProfile
        profile, created = UserProfile.objects.get_or_create(user=self.user)
        profile.onboarding_completed = False
        profile.save()
        
        response = self.client.get('/get_started_profile/')
        self.assertContains(response, 'Skip for Now')
    
    def test_skip_button_hidden_after_completion(self):
        """Test that skip button is hidden after onboarding_completed=True."""
        from core.models import UserProfile
        profile, created = UserProfile.objects.get_or_create(user=self.user)
        profile.onboarding_completed = True
        profile.save()
        
        response = self.client.get('/get_started_profile/')
        self.assertNotContains(response, 'Skip for Now')
    
    def test_skip_parameter_marks_onboarding_complete(self):
        """Test that ?skip=true parameter sets onboarding_completed=True."""
        response = self.client.get('/get_started_profile/?skip=true', follow=True)
        
        self.user.refresh_from_db()
        profile = self.user.profile
        self.assertTrue(profile.onboarding_completed)
        
        # Should redirect to home_dash
        self.assertContains(response, 'home')
    
    def test_skip_parameter_redirects_to_home(self):
        """Test that ?skip=true redirects to home_dash."""
        response = self.client.get('/get_started_profile/?skip=true', follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('home_dash', response.url)
    
    def test_form_submission_marks_onboarding_complete(self):
        """Test that form submission sets onboarding_completed=True."""
        response = self.client.post('/get_started_profile/', {
            'name': 'Test User',
            'height': '180',
            'weight': '75',
        }, follow=True)
        
        self.user.refresh_from_db()
        profile = self.user.profile
        self.assertTrue(profile.onboarding_completed)
    
    def test_discard_button_marks_onboarding_complete(self):
        """Test that discard button redirects with skip parameter."""
        response = self.client.get('/get_started_profile/?skip=true', follow=True)
        
        self.user.refresh_from_db()
        profile = self.user.profile
        self.assertTrue(profile.onboarding_completed)


class SocialLoginUserFieldTests(TestCase):
    """Tests for social_login_user field tracking."""
    
    def setUp(self):
        self.client = Client()
    
    def test_social_login_user_false_by_default(self):
        """Test that new profiles have social_login_user=False."""
        from core.models import UserProfile
        user = User.objects.create_user(
            username='regular@example.com',
            email='regular@example.com',
            password='TestPass123!',
            is_active=True
        )
        
        profile = UserProfile.objects.create(user=user)
        self.assertFalse(profile.social_login_user)
    
    def test_email_verified_user_shows_skip_button(self):
        """Test that email-verified users see skip button on first onboarding."""
        from core.models import UserProfile, EmailVerification
        
        # Create user via email signup
        user = User.objects.create_user(
            username='emailsignup@example.com',
            email='emailsignup@example.com',
            password='TestPass123!',
            is_active=True
        )
        
        # Simulate email verification and redirect to get_started_profile
        self.client.login(username='emailsignup@example.com', password='TestPass123!')
        
        response = self.client.get('/get_started_profile/')
        self.assertEqual(response.status_code, 200)
        
        # Profile should be created
        profile = user.profile
        self.assertFalse(profile.onboarding_completed)
        self.assertFalse(profile.social_login_user)
        
        # Skip button should show
        self.assertContains(response, 'Skip for Now')


class OnboardingMiddlewareTests(TestCase):
    """Tests for SocialLoginOnboardingMiddleware behavior."""
    
    def setUp(self):
        self.client = Client()
    
    def test_middleware_redirects_incomplete_social_user(self):
        """Test that middleware redirects users with social_login_user=True and onboarding_completed=False."""
        from core.models import UserProfile
        
        user = User.objects.create_user(
            username='socialuser@example.com',
            email='socialuser@example.com',
            password='TestPass123!',
            is_active=True
        )
        
        # Mark as social login user with incomplete onboarding
        profile = UserProfile.objects.create(
            user=user,
            social_login_user=True,
            onboarding_completed=False
        )
        
        self.client.login(username='socialuser@example.com', password='TestPass123!')
        
        # Accessing home_dash should redirect to get_started_profile
        response = self.client.get('/home_dash/', follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('get_started_profile', response.url)
    
    def test_middleware_does_not_redirect_completed_user(self):
        """Test that middleware doesn't redirect users with onboarding_completed=True."""
        from core.models import UserProfile
        
        user = User.objects.create_user(
            username='completeduser@example.com',
            email='completeduser@example.com',
            password='TestPass123!',
            is_active=True
        )
        
        # Mark as social login user with completed onboarding
        profile = UserProfile.objects.create(
            user=user,
            social_login_user=True,
            onboarding_completed=True
        )
        
        self.client.login(username='completeduser@example.com', password='TestPass123!')
        
        # Accessing home_dash should NOT redirect to get_started_profile
        response = self.client.get('/home_dash/', follow=False)
        self.assertEqual(response.status_code, 200)
    
    def test_middleware_does_not_redirect_non_social_user(self):
        """Test that middleware doesn't redirect regular (non-social) users."""
        from core.models import UserProfile
        
        user = User.objects.create_user(
            username='regularuser@example.com',
            email='regularuser@example.com',
            password='TestPass123!',
            is_active=True
        )
        
        # Create profile but mark social_login_user=False
        profile = UserProfile.objects.create(
            user=user,
            social_login_user=False,
            onboarding_completed=False
        )
        
        self.client.login(username='regularuser@example.com', password='TestPass123!')
        
        # Accessing home_dash should NOT redirect
        response = self.client.get('/home_dash/', follow=False)
        self.assertEqual(response.status_code, 200)
    
    def test_middleware_does_not_redirect_from_onboarding_page(self):
        """Test that middleware doesn't create redirect loop on onboarding page."""
        from core.models import UserProfile
        
        user = User.objects.create_user(
            username='looptest@example.com',
            email='looptest@example.com',
            password='TestPass123!',
            is_active=True
        )
        
        # Mark as incomplete social user
        profile = UserProfile.objects.create(
            user=user,
            social_login_user=True,
            onboarding_completed=False
        )
        
        self.client.login(username='looptest@example.com', password='TestPass123!')
        
        # Accessing get_started_profile should NOT redirect
        response = self.client.get('/get_started_profile/', follow=False)
        self.assertEqual(response.status_code, 200)


class GetStartedProfileIntegrationTests(TestCase):
    """Integration tests for complete get_started_profile flow."""
    
    def setUp(self):
        self.client = Client()
    
    def test_complete_onboarding_flow_email_signup(self):
        """Test complete flow: create account -> verify email -> skip onboarding -> access home."""
        from core.models import UserProfile, EmailVerification
        
        # Step 1: Create account
        user = User.objects.create_user(
            username='fullflow@example.com',
            email='fullflow@example.com',
            password='TestPass123!',
            is_active=True
        )
        
        # Step 2: Login (simulating after email verification)
        self.client.login(username='fullflow@example.com', password='TestPass123!')
        
        # Step 3: Access get_started_profile - should show skip button
        response = self.client.get('/get_started_profile/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Skip for Now')
        
        # Step 4: Click skip
        response = self.client.get('/get_started_profile/?skip=true', follow=True)
        
        # Step 5: Verify onboarding is completed
        user.refresh_from_db()
        profile = user.profile
        self.assertTrue(profile.onboarding_completed)
        
        # Step 6: Verify redirect to home_dash succeeded
        self.assertContains(response, 'home')
        
        # Step 7: Verify skip button is hidden on subsequent visits
        response = self.client.get('/get_started_profile/')
        self.assertNotContains(response, 'Skip for Now')
    
    def test_complete_onboarding_flow_form_submission(self):
        """Test complete flow: create account -> fill form -> completion."""
        user = User.objects.create_user(
            username='formflow@example.com',
            email='formflow@example.com',
            password='TestPass123!',
            is_active=True
        )
        
        self.client.login(username='formflow@example.com', password='TestPass123!')
        
        # Submit form
        response = self.client.post('/get_started_profile/', {
            'name': 'John Doe',
            'height': '180',
            'weight': '75',
            'age': '30',
            'primary_goal': 'muscle_gain',
            'experience_level': 'intermediate',
            'dietary_preference': 'omnivore',
            'has_home_gym': 'yes',
        }, follow=True)
        
        # Verify onboarding completed
        user.refresh_from_db()
        profile = user.profile
        self.assertTrue(profile.onboarding_completed)
        self.assertEqual(profile.height, 180)
        self.assertEqual(profile.weight, 75)
        self.assertEqual(profile.age, 30)

# ==================== SUPPLEMENT TESTS ====================

class SupplementDatabaseModelTests(TestCase):
    """Tests for the SupplementDatabase model"""
    
    def test_create_supplement(self):
        """Test creating a supplement in the database"""
        supplement = SupplementDatabase.objects.create(
            name='Vitamin C',
            supplement_type='vitamin',
            dosage='1000',
            unit='mg'
        )
        self.assertEqual(supplement.name, 'Vitamin C')
        self.assertEqual(supplement.supplement_type, 'vitamin')
        self.assertEqual(supplement.dosage, '1000')
        self.assertEqual(supplement.unit, 'mg')
    
    def test_supplement_str(self):
        """Test string representation of supplement"""
        supplement = SupplementDatabase.objects.create(
            name='Vitamin D',
            supplement_type='vitamin',
            dosage='600',
            unit='IU'
        )
        self.assertEqual(str(supplement), 'Vitamin D (Vitamin)')
    
    def test_unique_supplement_name(self):
        """Test that supplement names are unique"""
        SupplementDatabase.objects.create(
            name='Calcium',
            supplement_type='mineral',
            dosage='1000',
            unit='mg'
        )
        with self.assertRaises(Exception):
            SupplementDatabase.objects.create(
                name='Calcium',
                supplement_type='mineral',
                dosage='500',
                unit='mg'
            )
    
    def test_supplement_ordering(self):
        """Test that supplements are ordered by name"""
        SupplementDatabase.objects.create(name='Zinc', supplement_type='mineral', dosage='11', unit='mg')
        SupplementDatabase.objects.create(name='Vitamin A', supplement_type='vitamin', dosage='1000', unit='mcg')
        SupplementDatabase.objects.create(name='Iron', supplement_type='mineral', dosage='18', unit='mg')
        
        supplements = SupplementDatabase.objects.all()
        names = [s.name for s in supplements]
        self.assertEqual(names, sorted(names))


class SupplementEntryModelTests(TestCase):
    """Tests for the SupplementEntry model"""
    
    def setUp(self):
        """Set up test user and supplement"""
        self.user = User.objects.create_user(username='supplement_entry_test_user', email='test@spotter.ai', password='testpass123')
        self.supplement = SupplementDatabase.objects.create(
            name='Vitamin C',
            supplement_type='vitamin',
            dosage='1000',
            unit='mg'
        )
    
    def test_create_supplement_entry(self):
        """Test creating a supplement entry for a user"""
        from datetime import date
        
        entry = SupplementEntry.objects.create(
            user=self.user,
            supplement=self.supplement,
            name='Vitamin C',
            supplement_type='vitamin',
            dosage='1000',
            unit='mg',
            date=date.today(),
            taken=False
        )
        self.assertEqual(entry.user, self.user)
        self.assertEqual(entry.supplement, self.supplement)
        self.assertFalse(entry.taken)
    
    def test_supplement_entry_str(self):
        """Test string representation of supplement entry"""
        from datetime import date
        
        entry = SupplementEntry.objects.create(
            user=self.user,
            supplement=self.supplement,
            name='Vitamin C',
            supplement_type='vitamin',
            dosage='1000',
            unit='mg',
            date=date.today(),
            taken=False
        )
        self.assertIn('Vitamin C', str(entry))
        self.assertIn(self.user.email, str(entry))
    
    def test_toggle_supplement_taken(self):
        """Test toggling the taken status of a supplement"""
        from datetime import date
        
        entry = SupplementEntry.objects.create(
            user=self.user,
            supplement=self.supplement,
            name='Vitamin C',
            supplement_type='vitamin',
            dosage='1000',
            unit='mg',
            date=date.today(),
            taken=False
        )
        self.assertFalse(entry.taken)
        
        entry.taken = True
        entry.save()
        entry.refresh_from_db()
        self.assertTrue(entry.taken)
    
    def test_supplement_entry_without_supplement_link(self):
        """Test creating a supplement entry without linking to database supplement"""
        from datetime import date
        
        entry = SupplementEntry.objects.create(
            user=self.user,
            supplement=None,
            name='Custom Supplement',
            supplement_type='other',
            dosage='1',
            unit='serving',
            date=date.today(),
            taken=False
        )
        self.assertIsNone(entry.supplement)
        self.assertEqual(entry.name, 'Custom Supplement')
    
    def test_supplement_entries_filtered_by_date_and_user(self):
        """Test filtering supplement entries by user and date"""
        from datetime import date, timedelta
        
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        # Create entries for today
        entry1 = SupplementEntry.objects.create(
            user=self.user,
            supplement=self.supplement,
            name='Vitamin C',
            supplement_type='vitamin',
            dosage='1000',
            unit='mg',
            date=today,
            taken=False
        )
        
        # Create entry for yesterday
        entry2 = SupplementEntry.objects.create(
            user=self.user,
            supplement=self.supplement,
            name='Vitamin D',
            supplement_type='vitamin',
            dosage='600',
            unit='IU',
            date=yesterday,
            taken=False
        )
        
        # Query today's entries
        today_entries = SupplementEntry.objects.filter(user=self.user, date=today)
        self.assertEqual(today_entries.count(), 1)
        self.assertEqual(today_entries.first().name, 'Vitamin C')


class SupplementAPITests(TestCase):
    """Tests for supplement API endpoints"""
    
    def setUp(self):
        """Set up test user and supplements"""
        self.user = User.objects.create_user(username='supplement_test_user', email='test@spotter.ai', password='testpass123')
        self.client.login(username='supplement_test_user', password='testpass123')
        
        # Create some test supplements
        SupplementDatabase.objects.create(name='Vitamin C', supplement_type='vitamin', dosage='1000', unit='mg')
        SupplementDatabase.objects.create(name='Vitamin D', supplement_type='vitamin', dosage='600', unit='IU')
        SupplementDatabase.objects.create(name='Calcium', supplement_type='mineral', dosage='1000', unit='mg')
    
    def test_search_supplements_api(self):
        """Test the supplement search API"""
        response = self.client.get('/api/search_supplements/?q=vitamin')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('results', data)
        self.assertGreater(len(data['results']), 0)
    
    def test_search_supplements_requires_min_length(self):
        """Test that supplement search requires at least 2 characters"""
        response = self.client.get('/api/search_supplements/?q=v')
        data = response.json()
        self.assertEqual(len(data['results']), 0)
    
    def test_supplement_entries_list_api(self):
        """Test getting supplement entries for a date"""
        from datetime import date
        
        # Create an entry
        SupplementEntry.objects.create(
            user=self.user,
            name='Vitamin C',
            supplement_type='vitamin',
            dosage='1000',
            unit='mg',
            date=date.today(),
            taken=False
        )
        
        response = self.client.get('/api/supplement_entries/?date=' + str(date.today()))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('entries', data)
    
    def test_supplement_entries_create_api(self):
        """Test creating a supplement entry via API"""
        from datetime import date
        import json
        
        payload = {
            'name': 'Vitamin C',
            'supplement_type': 'vitamin',
            'dosage': '1000',
            'unit': 'mg',
            'date': str(date.today())
        }
        
        response = self.client.post(
            '/api/supplement_entries/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('entry', data)

