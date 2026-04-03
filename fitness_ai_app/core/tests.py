import uuid
import smtplib
import unittest
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.utils import timezone

from .models import EmailVerification
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
        self.assertIn('home_dash', r.url)
        r2 = self.client.get('/home_dash/')
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
        r = self.client.post('/nutrition/add_meal/', {
            'meal_name': '',
            'date': '2025-06-15',
        })
        self.assertEqual(r.status_code, 302)
        self.assertFalse(Meal.objects.exists())

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



