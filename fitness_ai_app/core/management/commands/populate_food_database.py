from django.core.management.base import BaseCommand
from core.models import FoodDatabase


class Command(BaseCommand):
    help = 'Populate the food database with common foods (nutritional values per 100g)'

    def handle(self, *args, **options):
        # (name, calories, protein, carbs, fats) — all per 100g serving
        foods = [
            # Proteins
            ('Chicken Breast', 165, 31.0, 0.0, 3.6),
            ('Ground Beef (80/20)', 254, 17.0, 0.0, 20.0),
            ('Canned Tuna', 116, 26.0, 0.0, 1.0),
            ('Salmon', 208, 20.0, 0.0, 13.0),
            ('Egg (whole)', 155, 13.0, 1.1, 11.0),
            ('Turkey Breast', 135, 30.0, 0.0, 1.0),
            ('Pork Loin', 242, 27.0, 0.0, 14.0),
            ('Shrimp', 99, 24.0, 0.0, 0.3),
            ('Tofu (firm)', 76, 8.0, 1.9, 4.8),
            ('Tilapia', 96, 20.0, 0.0, 1.7),
            ('Cod', 82, 18.0, 0.0, 0.7),
            ('Ground Turkey', 149, 19.0, 0.0, 7.7),

            # Dairy
            ('Whole Milk', 61, 3.2, 4.8, 3.3),
            ('Cheddar Cheese', 403, 25.0, 1.3, 33.0),
            ('Greek Yogurt (plain)', 97, 9.0, 3.6, 5.0),
            ('Cottage Cheese', 98, 11.0, 3.4, 4.3),
            ('Mozzarella', 280, 28.0, 2.2, 17.0),
            ('Cream Cheese', 342, 6.0, 4.1, 34.0),
            ('Skim Milk', 34, 3.4, 5.0, 0.1),

            # Grains & Starches
            ('White Rice (cooked)', 130, 2.7, 28.0, 0.3),
            ('Brown Rice (cooked)', 122, 2.6, 26.0, 1.0),
            ('Oats (dry)', 389, 17.0, 66.0, 7.0),
            ('White Bread', 265, 9.0, 49.0, 3.2),
            ('Whole Wheat Bread', 247, 13.0, 41.0, 4.2),
            ('Pasta (cooked)', 131, 5.0, 25.0, 1.1),
            ('Quinoa (cooked)', 120, 4.4, 22.0, 1.9),
            ('Bagel (plain)', 245, 10.0, 48.0, 1.5),
            ('Tortilla (flour)', 313, 8.0, 53.0, 7.3),
            ('Granola', 489, 12.0, 67.0, 20.0),
            ('Cornflakes Cereal', 357, 7.5, 84.0, 0.4),

            # Vegetables
            ('Broccoli', 34, 2.8, 7.0, 0.4),
            ('Spinach', 23, 2.9, 3.6, 0.4),
            ('Sweet Potato', 86, 1.6, 20.0, 0.1),
            ('Carrot', 41, 0.9, 10.0, 0.2),
            ('Tomato', 18, 0.9, 3.9, 0.2),
            ('Cucumber', 15, 0.7, 3.6, 0.1),
            ('Bell Pepper', 31, 1.0, 6.0, 0.3),
            ('Kale', 49, 4.3, 9.0, 0.9),
            ('Corn (cooked)', 86, 3.2, 19.0, 1.2),
            ('Edamame', 121, 11.0, 9.0, 5.0),
            ('Zucchini', 17, 1.2, 3.1, 0.3),
            ('Mushrooms', 22, 3.1, 3.3, 0.3),
            ('Green Beans', 31, 1.8, 7.0, 0.1),
            ('Asparagus', 20, 2.2, 3.9, 0.1),
            ('Cauliflower', 25, 1.9, 5.0, 0.3),
            ('Brussels Sprouts', 43, 3.4, 9.0, 0.3),

            # Fruits
            ('Banana', 89, 1.1, 23.0, 0.3),
            ('Apple', 52, 0.3, 14.0, 0.2),
            ('Orange', 47, 0.9, 12.0, 0.1),
            ('Strawberries', 32, 0.7, 7.7, 0.3),
            ('Blueberries', 57, 0.7, 14.0, 0.3),
            ('Avocado', 160, 2.0, 9.0, 15.0),
            ('Mango', 60, 0.8, 15.0, 0.4),
            ('Grapes', 69, 0.7, 18.0, 0.2),
            ('Pineapple', 50, 0.5, 13.0, 0.1),
            ('Watermelon', 30, 0.6, 7.6, 0.2),
            ('Peach', 39, 0.9, 10.0, 0.3),
            ('Raspberries', 52, 1.2, 12.0, 0.7),

            # Legumes
            ('Black Beans (cooked)', 132, 8.9, 24.0, 0.5),
            ('Lentils (cooked)', 116, 9.0, 20.0, 0.4),
            ('Chickpeas (cooked)', 164, 8.9, 27.0, 2.6),
            ('Kidney Beans (cooked)', 127, 8.7, 23.0, 0.5),
            ('Peas', 81, 5.4, 14.0, 0.4),

            # Nuts, Seeds & Butters
            ('Almonds', 579, 21.0, 22.0, 50.0),
            ('Walnuts', 654, 15.0, 14.0, 65.0),
            ('Cashews', 553, 18.0, 30.0, 44.0),
            ('Peanut Butter', 588, 25.0, 20.0, 50.0),
            ('Almond Butter', 614, 21.0, 19.0, 56.0),
            ('Chia Seeds', 486, 17.0, 42.0, 31.0),
            ('Sunflower Seeds', 584, 21.0, 20.0, 51.0),
            ('Flaxseeds', 534, 18.0, 29.0, 42.0),

            # Oils & Fats
            ('Olive Oil', 884, 0.0, 0.0, 100.0),
            ('Butter', 717, 0.9, 0.1, 81.0),
            ('Coconut Oil', 862, 0.0, 0.0, 100.0),

            # Sweets & Other
            ('Dark Chocolate (70%)', 546, 5.0, 60.0, 31.0),
            ('Honey', 304, 0.3, 82.0, 0.0),
            ('Hummus', 166, 7.9, 14.0, 9.6),
            ('Protein Bar (generic)', 370, 20.0, 45.0, 10.0),
            ('White Potato (baked)', 93, 2.5, 21.0, 0.1),
        ]

        created_count = 0
        for name, calories, protein, carbs, fats in foods:
            _, created = FoodDatabase.objects.get_or_create(
                name=name,
                defaults={
                    'calories': calories,
                    'protein': protein,
                    'carbs': carbs,
                    'fats': fats,
                    'serving_size': 100,
                    'serving_unit': 'grams',
                }
            )
            if created:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} food items. '
                f'Total foods in database: {FoodDatabase.objects.count()}'
            )
        )
