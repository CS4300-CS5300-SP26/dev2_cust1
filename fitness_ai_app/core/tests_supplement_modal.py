"""Test the supplement modal feature"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from core.models import Meal, SupplementDatabase, MealSupplement
from datetime import date


class SupplementModalFeatureTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
        # Create supplement
        self.supplement = SupplementDatabase.objects.create(
            name='Vitamin C',
            supplement_type='vitamin',
            dosage='500',
            unit='mg'
        )
        
        # Create meal
        self.meal = Meal.objects.create(
            user=self.user,
            name='Lunch',
            date=date.today()
        )
    
    def test_nutrition_page_has_modal(self):
        """Test that nutrition page loads with modal"""
        response = self.client.get('/nutrition/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'addItemModal', response.content)
        self.assertIn(b'openAddItemModal', response.content)
    
    def test_add_supplement_to_meal_view(self):
        """Test adding supplement to meal"""
        response = self.client.post(
            '/nutrition/add_supplement_to_meal/',
            {
                'meal_id': self.meal.id,
                'supplement_name': 'Vitamin C',
                'supplement_type': 'vitamin',
                'dosage': '500',
                'unit': 'mg',
                'date': date.today().strftime('%Y-%m-%d')
            }
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertTrue(MealSupplement.objects.filter(meal=self.meal).exists())
    
    def test_toggle_supplement_taken(self):
        """Test toggling supplement taken status"""
        supplement = MealSupplement.objects.create(
            meal=self.meal,
            name='Vitamin C',
            supplement_type='vitamin',
            dosage='500',
            unit='mg',
            taken=False
        )
        
        response = self.client.post(
            '/nutrition/toggle_meal_supplement/',
            {
                'supplement_id': supplement.id,
                'date': date.today().strftime('%Y-%m-%d')
            }
        )
        
        self.assertEqual(response.status_code, 302)
        supplement.refresh_from_db()
        self.assertTrue(supplement.taken)
    
    def test_delete_supplement_from_meal(self):
        """Test deleting supplement from meal"""
        supplement = MealSupplement.objects.create(
            meal=self.meal,
            name='Vitamin C',
            supplement_type='vitamin',
            dosage='500',
            unit='mg'
        )
        
        response = self.client.post(
            '/nutrition/delete_meal_supplement/',
            {
                'supplement_id': supplement.id,
                'date': date.today().strftime('%Y-%m-%d')
            }
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertFalse(MealSupplement.objects.filter(id=supplement.id).exists())
