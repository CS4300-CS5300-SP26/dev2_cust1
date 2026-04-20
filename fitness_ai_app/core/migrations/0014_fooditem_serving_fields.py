"""Re-introduce FoodItem.serving_size and serving_unit fields.

On the legacy dev DB these columns already exist (NOT NULL), so we only update
the migration state there.  On a fresh DB (CI, new dev machines) the columns
must actually be created.  We use RunPython with a column-existence check so
the migration is safe to apply in both situations.
"""

from django.db import migrations, models


def _add_serving_columns(apps, schema_editor):
    conn = schema_editor.connection
    if conn.vendor == 'sqlite':
        with conn.cursor() as cur:
            cur.execute("PRAGMA table_info(core_fooditem)")
            existing = {row[1] for row in cur.fetchall()}
        if 'serving_size' not in existing:
            schema_editor.execute(
                "ALTER TABLE core_fooditem ADD COLUMN serving_size "
                "DECIMAL(8, 2) NOT NULL DEFAULT 1"
            )
        if 'serving_unit' not in existing:
            schema_editor.execute(
                "ALTER TABLE core_fooditem ADD COLUMN serving_unit "
                "VARCHAR(20) NOT NULL DEFAULT 'serving'"
            )
    else:
        # PostgreSQL / other: check information_schema
        with conn.cursor() as cur:
            cur.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='core_fooditem'"
            )
            existing = {row[0] for row in cur.fetchall()}
        if 'serving_size' not in existing:
            schema_editor.execute(
                "ALTER TABLE core_fooditem ADD COLUMN serving_size "
                "NUMERIC(8, 2) NOT NULL DEFAULT 1"
            )
        if 'serving_unit' not in existing:
            schema_editor.execute(
                "ALTER TABLE core_fooditem ADD COLUMN serving_unit "
                "VARCHAR(20) NOT NULL DEFAULT 'serving'"
            )


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
            database_operations=[
                migrations.RunPython(
                    _add_serving_columns,
                    migrations.RunPython.noop,
                ),
            ],
        ),
    ]
