from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_fooditem_serving_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='FoodGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('meal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='food_groups', to='core.meal')),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
        migrations.AddField(
            model_name='fooditem',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='grouped_items', to='core.foodgroup'),
        ),
    ]
