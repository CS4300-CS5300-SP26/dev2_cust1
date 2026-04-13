from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_supplementdatabase_supplemententry_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='MealSupplement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('supplement_type', models.CharField(choices=[('vitamin', 'Vitamin'), ('mineral', 'Mineral'), ('herb', 'Herbal'), ('protein', 'Protein'), ('amino_acid', 'Amino Acid'), ('other', 'Other')], max_length=20)),
                ('dosage', models.CharField(max_length=100)),
                ('unit', models.CharField(max_length=50)),
                ('taken', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('meal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='supplements', to='core.meal')),
                ('supplement', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.supplementdatabase')),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
    ]
