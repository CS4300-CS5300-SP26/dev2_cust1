from django.core.management.base import BaseCommand
from core.models import SupplementDatabase


class Command(BaseCommand):
    help = 'Populate the supplement database with common vitamins, minerals, and supplements'

    def handle(self, *args, **options):
        supplements = [
            # Vitamins
            ('Vitamin A', 'vitamin', '1000', 'mcg'),
            ('Vitamin B1 (Thiamine)', 'vitamin', '1.5', 'mg'),
            ('Vitamin B2 (Riboflavin)', 'vitamin', '1.7', 'mg'),
            ('Vitamin B3 (Niacin)', 'vitamin', '16', 'mg'),
            ('Vitamin B5 (Pantothenic Acid)', 'vitamin', '5', 'mg'),
            ('Vitamin B6', 'vitamin', '2', 'mg'),
            ('Vitamin B7 (Biotin)', 'vitamin', '100', 'mcg'),
            ('Vitamin B9 (Folate)', 'vitamin', '400', 'mcg'),
            ('Vitamin B12', 'vitamin', '2.4', 'mcg'),
            ('Vitamin C', 'vitamin', '90', 'mg'),
            ('Vitamin D', 'vitamin', '600', 'IU'),
            ('Vitamin E', 'vitamin', '15', 'mg'),
            ('Vitamin K', 'vitamin', '120', 'mcg'),

            # Minerals
            ('Calcium', 'mineral', '1000', 'mg'),
            ('Iron', 'mineral', '18', 'mg'),
            ('Zinc', 'mineral', '11', 'mg'),
            ('Magnesium', 'mineral', '420', 'mg'),
            ('Potassium', 'mineral', '3500', 'mg'),
            ('Sodium', 'mineral', '2300', 'mg'),
            ('Phosphorus', 'mineral', '700', 'mg'),
            ('Iodine', 'mineral', '150', 'mcg'),
            ('Chromium', 'mineral', '35', 'mcg'),
            ('Manganese', 'mineral', '2.3', 'mg'),
            ('Copper', 'mineral', '900', 'mcg'),
            ('Selenium', 'mineral', '55', 'mcg'),

            # Herbal & Other
            ('Ashwagandha', 'herb', '500', 'mg'),
            ('Ginseng', 'herb', '400', 'mg'),
            ('Turmeric (Curcumin)', 'herb', '500', 'mg'),
            ('Omega-3 (Fish Oil)', 'herb', '1000', 'mg'),
            ('Ginger', 'herb', '500', 'mg'),
            ('Garlic', 'herb', '500', 'mg'),
            ('Green Tea Extract', 'herb', '250', 'mg'),

            # Protein & Amino Acids
            ('Whey Protein', 'protein', '25', 'g'),
            ('Casein Protein', 'protein', '25', 'g'),
            ('Plant-Based Protein', 'protein', '25', 'g'),
            ('BCAA (Branched-Chain Amino Acids)', 'amino_acid', '5', 'g'),
            ('Creatine Monohydrate', 'amino_acid', '5', 'g'),
            ('Beta-Alanine', 'amino_acid', '3', 'g'),
            ('L-Glutamine', 'amino_acid', '5', 'g'),
            ('L-Carnitine', 'amino_acid', '2', 'g'),
            ('Taurine', 'amino_acid', '1000', 'mg'),
        ]

        created_count = 0
        for name, supp_type, dosage, unit in supplements:
            obj, created = SupplementDatabase.objects.get_or_create(
                name=name,
                defaults={
                    'supplement_type': supp_type,
                    'dosage': dosage,
                    'unit': unit,
                }
            )
            if created:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} supplements. '
                f'Total supplements in database: {SupplementDatabase.objects.count()}'
            )
        )
