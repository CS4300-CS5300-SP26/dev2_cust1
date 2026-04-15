from django.contrib import admin
from .models import (
    EmailVerification, PasswordReset, Meal, FoodItem, Workout, Exercise,
    ExerciseType, MuscleGroup, Muscle, Equipment, TrainingExercise,
    UserInjury, UserEquipmentProfile
)


# ===== EXERCISE DATABASE ADMIN =====

@admin.register(ExerciseType)
class ExerciseTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']


@admin.register(MuscleGroup)
class MuscleGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']


@admin.register(Muscle)
class MuscleAdmin(admin.ModelAdmin):
    list_display = ['name', 'muscle_group', 'description']
    search_fields = ['name', 'muscle_group__name']
    list_filter = ['muscle_group']
    ordering = ['muscle_group', 'name']


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']


@admin.register(TrainingExercise)
class TrainingExerciseAdmin(admin.ModelAdmin):
    list_display = ['name', 'exercise_type', 'difficulty', 'location', 'is_active']
    search_fields = ['name', 'description']
    list_filter = ['exercise_type', 'difficulty', 'location', 'is_active', 'high_impact']
    filter_horizontal = ['muscle_groups', 'primary_muscles', 'secondary_muscles', 'equipment']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'instructions', 'difficulty', 'is_active')
        }),
        ('Classification', {
            'fields': ('exercise_type', 'muscle_groups', 'primary_muscles', 'secondary_muscles')
        }),
        ('Location & Equipment', {
            'fields': ('location', 'equipment')
        }),
        ('Default Settings', {
            'fields': ('default_sets', 'default_reps', 'default_duration_seconds')
        }),
        ('Injury Considerations', {
            'fields': ('high_impact', 'joint_stress')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(UserInjury)
class UserInjuryAdmin(admin.ModelAdmin):
    list_display = ['user', 'muscle', 'severity', 'start_date', 'end_date', 'is_active']
    search_fields = ['user__email', 'muscle__name']
    list_filter = ['severity', 'is_active', 'start_date']
    date_hierarchy = 'start_date'
    readonly_fields = ['created_at']


@admin.register(UserEquipmentProfile)
class UserEquipmentProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'location']
    search_fields = ['user__email']
    list_filter = ['location']
    filter_horizontal = ['equipment']
