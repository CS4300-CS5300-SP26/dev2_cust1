from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_alter_fooditem_group_cascade'),
        ('core', '0016_workout_current_session_seconds'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fooditem',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='grouped_items', to='core.foodgroup'),
        ),
    ]
