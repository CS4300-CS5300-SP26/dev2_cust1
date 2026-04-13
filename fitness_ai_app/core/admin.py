from django.contrib import admin
from .models import Meal, FoodItem, Workout, Exercise, SupplementDatabase, SupplementEntry, MealSupplement

@admin.register(Meal)
class MealAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'date', 'created_at')
    list_filter = ('date', 'user')
    search_fields = ('name', 'user__email')

@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'meal', 'calories', 'completed', 'created_at')
    list_filter = ('completed', 'created_at')
    search_fields = ('name', 'meal__user__email')

@admin.register(Workout)
class WorkoutAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'goal', 'status', 'date', 'created_at')
    list_filter = ('goal', 'status', 'date')
    search_fields = ('name', 'user__email')

@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('name', 'workout', 'muscle_group', 'sets', 'reps', 'completed')
    list_filter = ('muscle_group', 'completed')
    search_fields = ('name', 'workout__user__email')

@admin.register(SupplementDatabase)
class SupplementDatabaseAdmin(admin.ModelAdmin):
    list_display = ('name', 'supplement_type', 'dosage', 'unit', 'created_at')
    list_filter = ('supplement_type',)
    search_fields = ('name',)
    readonly_fields = ('created_at',)

@admin.register(SupplementEntry)
class SupplementEntryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'supplement_type', 'date', 'taken', 'created_at')
    list_filter = ('taken', 'date', 'supplement_type')
    search_fields = ('name', 'user__email')

@admin.register(MealSupplement)
class MealSupplementAdmin(admin.ModelAdmin):
    list_display = ('name', 'meal', 'supplement_type', 'taken', 'created_at')
    list_filter = ('taken', 'supplement_type')
    search_fields = ('name', 'meal__user__email')
