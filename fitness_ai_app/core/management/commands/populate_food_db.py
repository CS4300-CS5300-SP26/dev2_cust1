"""
Management command to populate the food database with common food items.
Usage: python manage.py populate_food_db
"""

from datetime import date

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from core.models import FoodItem, Meal


class Command(BaseCommand):
    help = 'Populate the food database with common food items and their nutritional data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting food database population...'))

        # Create system user and meal (same pattern as save_food_to_database view)
        self.stdout.write('Setting up system food database meal...')
        system_user, _ = User.objects.get_or_create(
            username='system@spotter.ai',
            defaults={'email': 'system@spotter.ai', 'is_active': False}
        )
        system_meal, _ = Meal.objects.get_or_create(
            user=system_user,
            name='Food Database',
            date=date(2000, 1, 1)
        )

        self.stdout.write('Creating food items...')
        foods_data = [
            # name, calories, protein(g), carbs(g), fats(g)
            # Proteins
            ('Grilled Chicken Breast (100g)', 165, 31, 0, 4),
            ('Salmon Fillet (100g)', 208, 20, 0, 13),
            ('Canned Tuna (100g)', 109, 25, 0, 1),
            ('Eggs (1 large)', 78, 6, 0, 5),
            ('Cottage Cheese (1 cup)', 206, 28, 8, 4),

            # Dairy
            ('Greek Yogurt Plain (170g)', 100, 17, 6, 0),
            ('Milk 2% (1 cup)', 122, 8, 12, 5),

            # Grains & Starches
            ('Brown Rice Cooked (1 cup)', 216, 5, 45, 2),
            ('Oatmeal Cooked (1 cup)', 166, 6, 28, 4),
            ('Quinoa Cooked (1 cup)', 222, 8, 39, 4),
            ('Whole Wheat Bread (1 slice)', 81, 4, 15, 1),
            ('Sweet Potato (1 medium)', 103, 2, 24, 0),

            # Vegetables
            ('Broccoli (1 cup)', 55, 4, 11, 0),
            ('Spinach Raw (1 cup)', 7, 1, 1, 0),

            # Legumes
            ('Black Beans (1 cup)', 227, 15, 41, 1),

            # Fruits
            ('Banana (1 medium)', 105, 1, 27, 0),
            ('Apple (1 medium)', 95, 0, 25, 0),

            # Fats & Nuts
            ('Almonds (28g)', 164, 6, 6, 14),
            ('Avocado (half)', 120, 2, 6, 11),
            ('Peanut Butter (2 tbsp)', 188, 8, 6, 16),
        ]

        for name, calories, protein, carbs, fats in foods_data:
            _, created = FoodItem.objects.get_or_create(
                meal=system_meal,
                name=name,
                defaults={
                    'calories': calories,
                    'protein': protein,
                    'carbs': carbs,
                    'fats': fats,
                    'completed': False,
                }
            )
            if created:
                self.stdout.write(f'✓ Created: {name}')
            else:
                self.stdout.write(f'→ Already exists: {name}')

        self.stdout.write(self.style.SUCCESS('✓ Food database population complete!'))
