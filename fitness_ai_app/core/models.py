from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    calorie_goal = models.PositiveIntegerField(default=2400)
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
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=200)
    calories = models.PositiveIntegerField()
    protein = models.PositiveIntegerField(default=0)
    carbs = models.PositiveIntegerField(default=0)
    fats = models.PositiveIntegerField(default=0)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.name} ({self.calories} kcal)"


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
