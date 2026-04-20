from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

class UserProfile(models.Model):
    PRIMARY_GOAL_CHOICES = [
        ('weight_loss', 'Weight Loss'),
        ('muscle_gain', 'Muscle Gain'),
        ('strength', 'Strength Training'),
        ('endurance', 'Endurance & Cardio'),
        ('flexibility', 'Flexibility & Mobility'),
        ('general_health', 'General Health & Wellness'),
    ]
    
    EXPERIENCE_LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    DIETARY_PREFERENCE_CHOICES = [
        ('omnivore', 'Omnivore'),
        ('vegetarian', 'Vegetarian'),
        ('vegan', 'Vegan'),
        ('keto', 'Keto'),
        ('paleo', 'Paleo'),
        ('gluten_free', 'Gluten-Free'),
    ]
    
    HOME_EQUIPMENT_CHOICES = [
        ('dumbbells', 'Dumbbells'),
        ('resistance_bands', 'Resistance Bands'),
        ('kettlebell', 'Kettlebell'),
        ('yoga_mat', 'Yoga Mat'),
        ('pull_up_bar', 'Pull-up Bar'),
        ('bench', 'Weight Bench'),
        ('treadmill', 'Treadmill'),
        ('stationary_bike', 'Stationary Bike'),
        ('jump_rope', 'Jump Rope'),
        ('medicine_ball', 'Medicine Ball'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    calorie_goal = models.PositiveIntegerField(default=2400)
    height = models.PositiveIntegerField(null=True, blank=True, help_text="Height in cm")
    weight = models.PositiveIntegerField(null=True, blank=True, help_text="Weight in kg")
    age = models.PositiveIntegerField(null=True, blank=True, help_text="Age in years")
    primary_goal = models.CharField(max_length=20, choices=PRIMARY_GOAL_CHOICES, null=True, blank=True)
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVEL_CHOICES, null=True, blank=True)
    dietary_preference = models.CharField(max_length=20, choices=DIETARY_PREFERENCE_CHOICES, null=True, blank=True)
    has_home_gym = models.BooleanField(null=True, blank=True, help_text="Does user have home gym setup")
    home_equipment = models.JSONField(default=list, blank=True, help_text="Available home exercise equipment")
    bio = models.TextField(null=True, blank=True, help_text="About you and your fitness journey")
    onboarding_completed = models.BooleanField(default=False, help_text="Whether user has completed the get_started_profile onboarding")
    social_login_user = models.BooleanField(default=False, help_text="Whether user came from a social login")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - Profile"


class EmailVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    verified = models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now() > self.created_at + timezone.timedelta(hours=24)


class PasswordReset(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_resets')
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    used = models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now() > self.created_at + timezone.timedelta(hours=24)


class Meal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meals')
    name = models.CharField(max_length=100)
    date = models.DateField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.user.email} - {self.date}"


class FoodItem(models.Model):
    SERVING_UNIT_CHOICES = [
        ('grams', 'Grams (g)'),
        ('ounces', 'Ounces (oz)'),
        ('cups', 'Cups'),
    ]

    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=200)
    calories = models.PositiveIntegerField()
    protein = models.PositiveIntegerField(default=0)
    carbs = models.PositiveIntegerField(default=0)
    fats = models.PositiveIntegerField(default=0)
    serving_size = models.DecimalField(max_digits=6, decimal_places=2, default=1, help_text="Number of servings")
    serving_unit = models.CharField(max_length=20, choices=SERVING_UNIT_CHOICES, default='grams', help_text="Unit of measurement for serving")
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.name} ({self.calories} kcal)"
    
    def get_adjusted_calories(self):
        return self.calories

    def get_adjusted_protein(self):
        return self.protein

    def get_adjusted_carbs(self):
        return self.carbs

    def get_adjusted_fats(self):
        return self.fats


class Workout(models.Model):
    GOAL_CHOICES = [
        ('strength', 'Strength Training'),
        ('weight_loss', 'Weight Loss'),
        ('flexibility', 'Flexibility'),
        ('cardio', 'Cardio Health'),
    ]

    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('completed', 'Completed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workouts')
    name = models.CharField(max_length=100)
    goal = models.CharField(max_length=20, choices=GOAL_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    date = models.DateField()
    total_duration_seconds = models.PositiveIntegerField(null=True, blank=True, help_text='Total workout duration in seconds')
    current_session_seconds = models.PositiveIntegerField(default=0, help_text='Current session timer in seconds')
    total_duration_seconds = models.PositiveIntegerField(null=True, blank=True, help_text="Total workout duration in seconds")
    current_session_seconds = models.PositiveIntegerField(default=0, help_text="Current session timer in seconds")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.name} - {self.get_goal_display()} - {self.date}"


class Exercise(models.Model):
    MUSCLE_GROUP_CHOICES = [
        ('arms', 'Arms'),
        ('chest', 'Chest'),
        ('back', 'Back'),
        ('shoulders', 'Shoulders'),
        ('legs', 'Legs'),
        ('core', 'Core'),
    ]

    workout = models.ForeignKey(Workout, on_delete=models.CASCADE, related_name='exercises')
    name = models.CharField(max_length=200)
    muscle_group = models.CharField(max_length=20, choices=MUSCLE_GROUP_CHOICES)
    sets = models.PositiveIntegerField(null=True, blank=True)
    reps = models.PositiveIntegerField(null=True, blank=True)
    weight = models.PositiveIntegerField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.name} - {self.get_muscle_group_display()}"


class SetProgress(models.Model):
    """Track completion status of individual sets within an exercise."""
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='set_progress')
    set_number = models.PositiveIntegerField()
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['set_number']
        unique_together = {('exercise', 'set_number')}

    def __str__(self):
        return f"Set {self.set_number} of {self.exercise.name}"
        unique_together = ('exercise', 'set_number')

    def __str__(self):
        return f"{self.exercise.name} - Set {self.set_number} - {'✓' if self.completed else '○'}"


# ===== EXERCISE DATABASE MODELS =====

class ExerciseType(models.Model):
    """Exercise classification by type (Strength, Cardio, etc.)"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class MuscleGroup(models.Model):
    """Primary muscle groups (Upper Body, Lower Body, etc.)"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Muscle(models.Model):
    """Specific muscles (Triceps, Biceps, etc.) for detailed tracking"""
    name = models.CharField(max_length=100, unique=True)
    muscle_group = models.ForeignKey(MuscleGroup, on_delete=models.CASCADE, related_name='muscles')
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['muscle_group', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.muscle_group.name})"


class Equipment(models.Model):
    """Equipment types available at home or gym"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class TrainingExercise(models.Model):
    """Main exercise database with comprehensive filtering"""
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    LOCATION_CHOICES = [
        ('home', 'At Home'),
        ('gym', 'At Gym'),
        ('both', 'Both Home & Gym'),
    ]
    
    # Basic info
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField()
    instructions = models.TextField(blank=True, help_text="Step-by-step exercise instructions")
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='intermediate')
    
    # Exercise classification
    exercise_type = models.ForeignKey(ExerciseType, on_delete=models.PROTECT, related_name='exercises')
    muscle_groups = models.ManyToManyField(MuscleGroup, related_name='training_exercises')
    primary_muscles = models.ManyToManyField(Muscle, related_name='primary_exercises')
    secondary_muscles = models.ManyToManyField(Muscle, related_name='secondary_exercises')
    
    # Location & Equipment
    location = models.CharField(max_length=20, choices=LOCATION_CHOICES, default='both')
    equipment = models.ManyToManyField(Equipment, blank=True, related_name='exercises')
    
    # Default rep/set schemes
    default_sets = models.PositiveIntegerField(default=3)
    default_reps = models.PositiveIntegerField(default=10)
    default_duration_seconds = models.PositiveIntegerField(null=True, blank=True, help_text="For timed exercises")
    
    # Injury considerations
    high_impact = models.BooleanField(default=False, help_text="Mark if exercise is high-impact")
    joint_stress = models.CharField(max_length=200, blank=True, help_text="Which joints are stressed (e.g., knees, shoulders)")
    
    # Admin
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['exercise_type', 'name']
        indexes = [
            models.Index(fields=['exercise_type', 'location']),
            models.Index(fields=['difficulty']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.exercise_type.name})"


class UserInjury(models.Model):
    """Track user injuries to exclude/modify exercises"""
    SEVERITY_CHOICES = [
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='injuries')
    muscle = models.ForeignKey(Muscle, on_delete=models.PROTECT)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    notes = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True, help_text="Leave blank if ongoing")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.user.email} - {self.muscle.name} ({self.get_severity_display()})"


class UserEquipmentProfile(models.Model):
    """Track equipment available to each user"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='equipment_profile')
    location = models.CharField(max_length=20, choices=[('home', 'At Home'), ('gym', 'At Gym'), ('both', 'Both')])
    equipment = models.ManyToManyField(Equipment, related_name='user_profiles')
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.get_location_display()}"


# ===== SUPPLEMENT MODELS =====

class SupplementDatabase(models.Model):
    TYPE_CHOICES = [
        ('vitamin', 'Vitamin'),
        ('mineral', 'Mineral'),
        ('herb', 'Herbal'),
        ('protein', 'Protein'),
        ('amino_acid', 'Amino Acid'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=200, unique=True, db_index=True)
    supplement_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    dosage = models.CharField(max_length=100, default='1')
    unit = models.CharField(max_length=50, default='serving')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['supplement_type']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_supplement_type_display()})"


class SupplementEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='supplement_entries')
    supplement = models.ForeignKey(SupplementDatabase, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=200)
    supplement_type = models.CharField(max_length=20, choices=SupplementDatabase.TYPE_CHOICES)
    dosage = models.CharField(max_length=100)
    unit = models.CharField(max_length=50)
    date = models.DateField()
    taken = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-date', 'name']
        indexes = [
            models.Index(fields=['user', 'date']),
        ]

    def __str__(self):
        return f"{self.name} - {self.user.email} - {self.date}"


class MealSupplement(models.Model):
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name='supplements')
    supplement = models.ForeignKey(SupplementDatabase, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=200)
    supplement_type = models.CharField(max_length=20, choices=SupplementDatabase.TYPE_CHOICES)
    dosage = models.CharField(max_length=100)
    unit = models.CharField(max_length=50)
    taken = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.name} - {self.meal.name}"


# ===== FOOD DATABASE =====

class FoodDatabase(models.Model):
    SERVING_UNIT_CHOICES = [
        ('grams', 'Grams (g)'),
        ('ounces', 'Ounces (oz)'),
        ('cups', 'Cups'),
    ]

    name = models.CharField(max_length=200, unique=True, db_index=True)
    calories = models.PositiveIntegerField()
    protein = models.DecimalField(max_digits=6, decimal_places=1, default=0)
    carbs = models.DecimalField(max_digits=6, decimal_places=1, default=0)
    fats = models.DecimalField(max_digits=6, decimal_places=1, default=0)
    serving_size = models.DecimalField(max_digits=6, decimal_places=1, default=100)
    serving_unit = models.CharField(max_length=20, choices=SERVING_UNIT_CHOICES, default='grams')

    class Meta:
        ordering = ['name']
        verbose_name = 'Food Database Entry'
        verbose_name_plural = 'Food Database'

    def __str__(self):
        return f"{self.name} ({self.calories} kcal per {self.serving_size}{self.serving_unit})"
