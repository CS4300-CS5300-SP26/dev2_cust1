from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_fooditem_serving_size_fooditem_serving_unit'),
    ]

    operations = [
        migrations.CreateModel(
            name='FoodDatabase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=200, unique=True)),
                ('calories', models.PositiveIntegerField()),
                ('protein', models.DecimalField(decimal_places=1, default=0, max_digits=6)),
                ('carbs', models.DecimalField(decimal_places=1, default=0, max_digits=6)),
                ('fats', models.DecimalField(decimal_places=1, default=0, max_digits=6)),
                ('serving_size', models.DecimalField(decimal_places=1, default=100, max_digits=6)),
                ('serving_unit', models.CharField(
                    choices=[('grams', 'Grams (g)'), ('ounces', 'Ounces (oz)'), ('cups', 'Cups')],
                    default='grams',
                    max_length=20,
                )),
            ],
            options={
                'verbose_name': 'Food Database Entry',
                'verbose_name_plural': 'Food Database',
                'ordering': ['name'],
            },
        ),
    ]
