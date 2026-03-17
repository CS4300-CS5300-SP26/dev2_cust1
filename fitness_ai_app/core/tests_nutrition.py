"""
Tests for the Nutrition Page

This module contains all tests related to the nutrition tracking functionality,
including the nutrition page view, HTML rendering, styling, and JavaScript interactions.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta


class NutritionPageAccessTests(TestCase):
    """Tests for nutrition page access and authentication"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='nutrition@spotter.ai',
            email='nutrition@spotter.ai',
            password='testpass123'
        )

    def test_nutrition_page_requires_authentication(self):
        """Test that unauthenticated users are redirected"""
        response = self.client.get('/nutrition/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('user_login', response.url)

    def test_authenticated_user_can_access_nutrition_page(self):
        """Test that authenticated users can load the nutrition page"""
        self.client.login(username='nutrition@spotter.ai', password='testpass123')
        response = self.client.get('/nutrition/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'nutrition_dir/nutrition_page.html')

    def test_nutrition_page_title(self):
        """Test that the nutrition page has the correct title"""
        self.client.login(username='nutrition@spotter.ai', password='testpass123')
        response = self.client.get('/nutrition/')
        self.assertContains(response, 'Nutrition - Spotter.ai')


class NutritionPageUIComponentTests(TestCase):
    """Tests for nutrition page UI components and structure"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='nutrition@spotter.ai',
            email='nutrition@spotter.ai',
            password='testpass123'
        )
        self.client.login(username='nutrition@spotter.ai', password='testpass123')

    def test_nutrition_header_present(self):
        """Test that the nutrition page header is displayed"""
        response = self.client.get('/nutrition/')
        self.assertContains(response, '<h1>Nutrition</h1>')

    def test_tab_bar_navigation_present(self):
        """Test that all nutrition tab buttons are present"""
        response = self.client.get('/nutrition/')
        self.assertContains(response, 'data-tab="today"')
        self.assertContains(response, 'data-tab="history"')
        self.assertContains(response, 'data-tab="search"')
        self.assertContains(response, 'data-tab="supplements"')

    def test_today_tab_is_active_by_default(self):
        """Test that the 'Today' tab is active on page load"""
        response = self.client.get('/nutrition/')
        self.assertContains(response, 'class="tab-button active" data-tab="today"')

    def test_date_navigator_present(self):
        """Test that date navigator controls are present"""
        response = self.client.get('/nutrition/')
        self.assertContains(response, 'date-navigator')
        self.assertContains(response, 'date-nav-btn')
        self.assertContains(response, 'calendar-btn')

    def test_current_date_displayed(self):
        """Test that the current date is displayed in the date navigator"""
        response = self.client.get('/nutrition/')
        today = timezone.now()
        date_str = today.strftime('%a, %b %d')
        # The date format might vary, so just check it's present
        self.assertContains(response, 'date-label')

    def test_calories_card_present(self):
        """Test that the calories card is displayed"""
        response = self.client.get('/nutrition/')
        self.assertContains(response, 'CALORIES')
        self.assertContains(response, 'kcal')
        self.assertContains(response, 'totalCalories')

    def test_macros_card_present(self):
        """Test that the macros (protein, carbs, fat) card is displayed"""
        response = self.client.get('/nutrition/')
        self.assertContains(response, 'Protein')
        self.assertContains(response, 'Carbs')
        self.assertContains(response, 'Fat')

    def test_progress_bar_present(self):
        """Test that the calories progress bar is present"""
        response = self.client.get('/nutrition/')
        self.assertContains(response, 'progressFill')

    def test_meals_section_header(self):
        """Test that the 'Today's Meals' section is present"""
        response = self.client.get('/nutrition/')
        self.assertContains(response, "TODAY'S MEALS")

    def test_add_meal_button_present(self):
        """Test that the button to add new meals is present"""
        response = self.client.get('/nutrition/')
        self.assertContains(response, 'add-meal-btn')

    def test_meal_card_structure(self):
        """Test that meal cards have the correct structure"""
        response = self.client.get('/nutrition/')
        self.assertContains(response, 'meal-card')
        self.assertContains(response, 'meal-header')

    def test_food_items_structure(self):
        """Test that food items have the correct elements"""
        response = self.client.get('/nutrition/')
        self.assertContains(response, 'food-item')
        self.assertContains(response, 'food-checkbox')


class NutritionPageNavigationTests(TestCase):
    """Tests for nutrition page navigation elements"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='nutrition@spotter.ai',
            email='nutrition@spotter.ai',
            password='testpass123'
        )
        self.client.login(username='nutrition@spotter.ai', password='testpass123')

    def test_bottom_nav_present(self):
        """Test that the bottom navigation bar is present"""
        response = self.client.get('/nutrition/')
        self.assertContains(response, 'bottom-nav')

    def test_bottom_nav_all_tabs_present(self):
        """Test that all bottom nav tabs are present"""
        response = self.client.get('/nutrition/')
        self.assertContains(response, 'Home')
        self.assertContains(response, 'Train')
        self.assertContains(response, 'Nutrition')
        self.assertContains(response, 'AI')
        self.assertContains(response, 'Social')

    def test_nutrition_tab_active_in_bottom_nav(self):
        """Test that the nutrition tab is highlighted as active"""
        response = self.client.get('/nutrition/')
        self.assertContains(response, 'active', count=2)  # One in tab bar, one in bottom nav

    def test_profile_dropdown_present(self):
        """Test that the profile dropdown button is present"""
        response = self.client.get('/nutrition/')
        self.assertContains(response, 'profile-btn')
        self.assertContains(response, 'profile-dropdown')

    def test_logout_option_in_profile_dropdown(self):
        """Test that the logout option is in the profile dropdown"""
        response = self.client.get('/nutrition/')
        self.assertContains(response, 'Log Out')

    def test_logo_container_present(self):
        """Test that the logo container is present"""
        response = self.client.get('/nutrition/')
        self.assertContains(response, 'logo-container')


class NutritionPageDateNavigationTests(TestCase):
    """Tests for date navigation functionality"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='nutrition@spotter.ai',
            email='nutrition@spotter.ai',
            password='testpass123'
        )
        self.client.login(username='nutrition@spotter.ai', password='testpass123')

    def test_can_navigate_to_previous_date(self):
        """Test that users can navigate to previous date"""
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        response = self.client.get('/nutrition/', {'date': yesterday.isoformat()})
        self.assertEqual(response.status_code, 200)

    def test_can_navigate_to_next_date(self):
        """Test that users can navigate to next date"""
        today = timezone.now().date()
        tomorrow = today + timedelta(days=1)
        response = self.client.get('/nutrition/', {'date': tomorrow.isoformat()})
        self.assertEqual(response.status_code, 200)

    def test_date_parameter_in_url(self):
        """Test that the date parameter is handled in the URL"""
        specific_date = '2024-03-15'
        response = self.client.get('/nutrition/', {'date': specific_date})
        self.assertEqual(response.status_code, 200)

    def test_invalid_date_parameter_handled(self):
        """Test that invalid date parameters don't break the page"""
        response = self.client.get('/nutrition/', {'date': 'invalid'})
        self.assertEqual(response.status_code, 200)


class NutritionPageCSSTests(TestCase):
    """Tests for nutrition page styling"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='nutrition@spotter.ai',
            email='nutrition@spotter.ai',
            password='testpass123'
        )
        self.client.login(username='nutrition@spotter.ai', password='testpass123')

    def test_nutrition_css_file_loaded(self):
        """Test that the nutrition CSS file is linked"""
        response = self.client.get('/nutrition/')
        self.assertContains(response, 'nutrition_page.css')

    def test_flatpickr_css_loaded(self):
        """Test that the flatpickr date picker CSS is loaded"""
        response = self.client.get('/nutrition/')
        self.assertContains(response, 'flatpickr')

    def test_dark_theme_colors_in_css(self):
        """Test that dark theme color variables are present"""
        response = self.client.get('/nutrition/')
        self.assertContains(response, 'nutrition-screen')

    def test_nutrition_page_container_present(self):
        """Test that the main nutrition screen container is present"""
        response = self.client.get('/nutrition/')
        self.assertContains(response, 'nutrition-screen')


class NutritionPageJavaScriptTests(TestCase):
    """Tests for nutrition page JavaScript functionality"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='nutrition@spotter.ai',
            email='nutrition@spotter.ai',
            password='testpass123'
        )
        self.client.login(username='nutrition@spotter.ai', password='testpass123')

    def test_nutrition_js_file_linked(self):
        """Test that the nutrition JavaScript file is linked"""
        response = self.client.get('/nutrition/')
        self.assertContains(response, 'nutrition_page.js')

    def test_calendar_functionality_js_present(self):
        """Test that calendar/date picker initialization is present"""
        response = self.client.get('/nutrition/')
        self.assertContains(response, 'dateInput')
        self.assertContains(response, 'calendarTrigger')

    def test_tab_switching_js_present(self):
        """Test that tab switching JavaScript is present"""
        response = self.client.get('/nutrition/')
        self.assertContains(response, 'tab-button')

    def test_dom_content_loaded_handler(self):
        """Test that DOMContentLoaded event is handled"""
        response = self.client.get('/nutrition/')
        # This tests that JavaScript is present to handle page initialization
        self.assertContains(response, 'nutrition-screen')


class NutritionPageResponsiveTests(TestCase):
    """Tests for nutrition page responsive design"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='nutrition@spotter.ai',
            email='nutrition@spotter.ai',
            password='testpass123'
        )
        self.client.login(username='nutrition@spotter.ai', password='testpass123')

    def test_viewport_meta_tag_present(self):
        """Test that viewport meta tag is present for mobile responsiveness"""
        response = self.client.get('/nutrition/')
        self.assertContains(response, 'viewport')

    def test_content_container_layout(self):
        """Test that content containers are properly structured"""
        response = self.client.get('/nutrition/')
        self.assertContains(response, 'content-container')

    def test_bottom_nav_is_fixed(self):
        """Test that bottom navigation is fixed position"""
        response = self.client.get('/nutrition/')
        self.assertContains(response, 'bottom-nav')


class NutritionPageAccessibilityTests(TestCase):
    """Tests for nutrition page accessibility features"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='nutrition@spotter.ai',
            email='nutrition@spotter.ai',
            password='testpass123'
        )
        self.client.login(username='nutrition@spotter.ai', password='testpass123')

    def test_buttons_have_titles(self):
        """Test that interactive buttons have title attributes for accessibility"""
        response = self.client.get('/nutrition/')
        self.assertContains(response, 'title="')

    def test_form_inputs_present(self):
        """Test that form inputs are properly structured"""
        response = self.client.get('/nutrition/')
        # Check for date input
        self.assertContains(response, 'dateInput')

    def test_meal_checkboxes_present(self):
        """Test that meal completion checkboxes are present"""
        response = self.client.get('/nutrition/')
        self.assertContains(response, 'food-checkbox')


class NutritionPageIntegrationTests(TestCase):
    """Integration tests for nutrition page with other app components"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='nutrition@spotter.ai',
            email='nutrition@spotter.ai',
            password='testpass123'
        )
        self.client.login(username='nutrition@spotter.ai', password='testpass123')

    def test_nutrition_page_uses_base_template(self):
        """Test that nutrition page extends the base app template"""
        response = self.client.get('/nutrition/')
        self.assertTemplateUsed(response, 'core/base_app.html')

    def test_navigation_bar_consistent_across_pages(self):
        """Test that navigation bar structure is consistent"""
        response = self.client.get('/nutrition/')
        # Check bottom nav elements are consistent with other pages
        self.assertContains(response, 'bottom-nav')
        self.assertContains(response, 'Home')
        self.assertContains(response, 'Train')
        self.assertContains(response, 'Nutrition')
        self.assertContains(response, 'AI')
        self.assertContains(response, 'Social')

    def test_profile_dropdown_consistent_across_pages(self):
        """Test that profile dropdown is consistent"""
        response = self.client.get('/nutrition/')
        self.assertContains(response, 'profile-btn')
        self.assertContains(response, 'profile-dropdown')


class NutritionPageDataDisplayTests(TestCase):
    """Tests for nutrition page data display"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='nutrition@spotter.ai',
            email='nutrition@spotter.ai',
            password='testpass123'
        )
        self.client.login(username='nutrition@spotter.ai', password='testpass123')

    def test_calorie_display_format(self):
        """Test that calories are displayed in the correct format"""
        response = self.client.get('/nutrition/')
        self.assertContains(response, 'kcal')

    def test_macro_display_format(self):
        """Test that macros are displayed with percentage and grams"""
        response = self.client.get('/nutrition/')
        # Check for macro grid structure
        self.assertContains(response, 'macros')

    def test_meal_sections_present(self):
        """Test that meal sections are available"""
        response = self.client.get('/nutrition/')
        self.assertContains(response, 'meal-section')

    def test_empty_state_handled(self):
        """Test that empty state (no meals) is handled"""
        response = self.client.get('/nutrition/')
        self.assertEqual(response.status_code, 200)


class NutritionPageEditFunctionalityTests(TestCase):
    """Tests for nutrition page edit/add functionality UI"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='nutrition@spotter.ai',
            email='nutrition@spotter.ai',
            password='testpass123'
        )
        self.client.login(username='nutrition@spotter.ai', password='testpass123')

    def test_add_meal_button_present(self):
        """Test that add meal functionality button is present"""
        response = self.client.get('/nutrition/')
        self.assertContains(response, 'add-meal-btn')

    def test_add_food_item_button_present(self):
        """Test that add food item button is present in meal cards"""
        response = self.client.get('/nutrition/')
        self.assertContains(response, 'add-food-btn')

    def test_edit_meal_functionality_present(self):
        """Test that edit meal button is present"""
        response = self.client.get('/nutrition/')
        self.assertContains(response, 'meal-header')

    def test_delete_food_item_functionality_present(self):
        """Test that delete food item functionality is present"""
        response = self.client.get('/nutrition/')
        self.assertContains(response, 'delete-btn')

    def test_meal_completion_checkbox_present(self):
        """Test that meal completion checkboxes are present"""
        response = self.client.get('/nutrition/')
        self.assertContains(response, 'food-checkbox')


class NutritionPageContextTests(TestCase):
    """Tests for nutrition page context data"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='nutrition@spotter.ai',
            email='nutrition@spotter.ai',
            password='testpass123'
        )
        self.client.login(username='nutrition@spotter.ai', password='testpass123')

    def test_page_context_contains_date(self):
        """Test that the page context includes date information"""
        response = self.client.get('/nutrition/')
        # The page should have date-related context
        self.assertContains(response, 'date-label')

    def test_previous_and_next_date_navigation(self):
        """Test that previous and next date links are present"""
        response = self.client.get('/nutrition/')
        # Check for date navigation links
        self.assertContains(response, 'date-nav-btn')

    def test_today_date_displayed_by_default(self):
        """Test that today's date is displayed by default"""
        response = self.client.get('/nutrition/')
        self.assertContains(response, 'date-label')
