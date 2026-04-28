from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0019_saved_nutrition_items"),
    ]

    operations = [
        migrations.AlterField(
            model_name="savedfood",
            name="id",
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"),
        ),
        migrations.AlterField(
            model_name="savedmeal",
            name="id",
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"),
        ),
        migrations.AlterField(
            model_name="savedsupplement",
            name="id",
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"),
        ),
    ]
