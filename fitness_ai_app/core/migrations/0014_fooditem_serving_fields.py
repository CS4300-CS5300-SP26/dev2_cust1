"""Re-introduce FoodItem.serving_size and serving_unit fields.

These columns exist in the legacy dev database with NOT NULL constraints but
were absent from the model state, causing IntegrityError on inserts. We add
them back at the state level only — the DB columns are already present, so no
schema change is needed.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_merge_20260417_1914'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='fooditem',
                    name='serving_size',
                    field=models.DecimalField(decimal_places=2, default=1, max_digits=8),
                ),
                migrations.AddField(
                    model_name='fooditem',
                    name='serving_unit',
                    field=models.CharField(default='serving', max_length=20),
                ),
            ],
            database_operations=[],
        ),
    ]
