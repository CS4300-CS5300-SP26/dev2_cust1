"""
Management command to populate the supplement database with common supplements.
Usage: python manage.py populate_supplements
"""

from django.core.management.base import BaseCommand

from core.models import SupplementDatabase


class Command(BaseCommand):
    help = 'Populate the supplement database with common vitamins, minerals, and supplements'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting supplement database population...'))

        # name, supplement_type, dosage, unit
        supplements_data = [
            # Vitamins
            ('Vitamin C', 'vitamin', '90', 'mg'),
            ('Vitamin D', 'vitamin', '600', 'IU'),
            ('Vitamin B12', 'vitamin', '2.4', 'mcg'),
            ('Vitamin A', 'vitamin', '1000', 'mcg'),
            ('Vitamin E', 'vitamin', '15', 'mg'),

            # Minerals
            ('Calcium', 'mineral', '1000', 'mg'),
            ('Magnesium', 'mineral', '420', 'mg'),
            ('Iron', 'mineral', '18', 'mg'),
            ('Zinc', 'mineral', '11', 'mg'),

            # Herbal & Other
            ('Omega-3 (Fish Oil)', 'herb', '1000', 'mg'),
            ('Ashwagandha', 'herb', '500', 'mg'),
            ('Turmeric (Curcumin)', 'herb', '500', 'mg'),

            # Protein
            ('Whey Protein', 'protein', '25', 'g'),
            ('Casein Protein', 'protein', '25', 'g'),
            ('Plant-Based Protein', 'protein', '25', 'g'),

            # Amino Acids
            ('Creatine Monohydrate', 'amino_acid', '5', 'g'),
            ('BCAA (Branched-Chain Amino Acids)', 'amino_acid', '5', 'g'),
            ('L-Glutamine', 'amino_acid', '5', 'g'),
            ('Beta-Alanine', 'amino_acid', '3', 'g'),
            ('L-Carnitine', 'amino_acid', '2', 'g'),
        ]

        self.stdout.write('Creating supplements...')
        for name, supp_type, dosage, unit in supplements_data:
            _, created = SupplementDatabase.objects.get_or_create(
                name=name,
                defaults={
                    'supplement_type': supp_type,
                    'dosage': dosage,
                    'unit': unit,
                }
            )
            if created:
                self.stdout.write(f'✓ Created: {name}')
            else:
                self.stdout.write(f'→ Already exists: {name}')

        self.stdout.write(self.style.SUCCESS('✓ Supplement database population complete!'))
