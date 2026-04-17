from types import MethodType

from django.contrib import admin

from .models import (
    EmailVerification,
    Equipment,
    Exercise,
    ExerciseType,
    FoodItem,
    Meal,
    MealSupplement,
    Muscle,
    MuscleGroup,
    PasswordReset,
    SupplementDatabase,
    SupplementEntry,
    TrainingExercise,
    UserEquipmentProfile,
    UserInjury,
    Workout,
)


def _grouped_core_get_app_list(self, request, app_label=None):
    app_list = self._original_get_app_list(request, app_label=app_label)
    organized = []

    for app in app_list:
        if app["app_label"] != "core":
            organized.append(app)
            continue

        core_models = app["models"]

        def model_key(model_dict):
            return model_dict.get("object_name", "").lower()

        sections = [
            ("Nutrition", "nutrition", {"meal", "fooditem", "mealsupplement"}),
            ("Workouts", "workouts", {"workout", "exercise"}),
            ("Supplements", "supplements", {"supplementdatabase", "supplemententry"}),
            (
                "Exercise Database",
                "exercise_database",
                {"trainingexercise", "exercisetype", "musclegroup", "muscle", "equipment"},
            ),
            (
                "User Preferences",
                "user_preferences",
                {"userinjury", "userequipmentprofile", "emailverification", "passwordreset"},
            ),
        ]

        matched = set()
        for title, slug, names in sections:
            models = [m for m in core_models if model_key(m) in names]
            if not models:
                continue

            matched.update(model_key(m) for m in models)
            organized.append(
                {
                    **app,
                    "name": f"Core / {title}",
                    "app_label": f"core_{slug}",
                    "models": models,
                }
            )

        leftovers = [m for m in core_models if model_key(m) not in matched]
        if leftovers:
            organized.append(
                {
                    **app,
                    "name": "Core / Other",
                    "app_label": "core_other",
                    "models": leftovers,
                }
            )

    return organized


if not hasattr(admin.site, "_core_grouping_patch_applied"):
    admin.site._original_get_app_list = admin.site.get_app_list
    admin.site.get_app_list = MethodType(_grouped_core_get_app_list, admin.site)
    admin.site.site_header = "Fitness AI Admin"
    admin.site.site_title = "Fitness AI Admin"
    admin.site.index_title = "Admin Dashboard"
    admin.site._core_grouping_patch_applied = True


@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ("user", "verified", "created_at")
    list_filter = ("verified", "created_at")
    search_fields = ("user__email", "user__username")
    readonly_fields = ("token", "created_at")


@admin.register(PasswordReset)
class PasswordResetAdmin(admin.ModelAdmin):
    list_display = ("user", "used", "created_at")
    list_filter = ("used", "created_at")
    search_fields = ("user__email", "user__username")
    readonly_fields = ("token", "created_at")


@admin.register(Meal)
class MealAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "date", "created_at")
    list_filter = ("date", "user")
    search_fields = ("name", "user__email")


@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ("name", "meal", "calories", "completed", "created_at")
    list_filter = ("completed", "created_at")
    search_fields = ("name", "meal__user__email")


@admin.register(MealSupplement)
class MealSupplementAdmin(admin.ModelAdmin):
    list_display = ("name", "meal", "supplement_type", "taken", "created_at")
    list_filter = ("taken", "supplement_type")
    search_fields = ("name", "meal__user__email")


@admin.register(Workout)
class WorkoutAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "goal", "status", "date", "created_at")
    list_filter = ("goal", "status", "date")
    search_fields = ("name", "user__email")


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ("name", "workout", "muscle_group", "sets", "reps", "completed")
    list_filter = ("muscle_group", "completed")
    search_fields = ("name", "workout__user__email")


@admin.register(SupplementDatabase)
class SupplementDatabaseAdmin(admin.ModelAdmin):
    list_display = ("name", "supplement_type", "dosage", "unit", "created_at")
    list_filter = ("supplement_type",)
    search_fields = ("name",)
    readonly_fields = ("created_at",)


@admin.register(SupplementEntry)
class SupplementEntryAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "supplement_type", "date", "taken", "created_at")
    list_filter = ("taken", "date", "supplement_type")
    search_fields = ("name", "user__email")


@admin.register(TrainingExercise)
class TrainingExerciseAdmin(admin.ModelAdmin):
    list_display = ["name", "exercise_type", "difficulty", "location", "is_active"]
    search_fields = ["name", "description"]
    list_filter = ["exercise_type", "difficulty", "location", "is_active", "high_impact"]
    filter_horizontal = ["muscle_groups", "primary_muscles", "secondary_muscles", "equipment"]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("name", "description", "instructions", "difficulty", "is_active")},
        ),
        (
            "Classification",
            {"fields": ("exercise_type", "muscle_groups", "primary_muscles", "secondary_muscles")},
        ),
        ("Location & Equipment", {"fields": ("location", "equipment")}),
        ("Default Settings", {"fields": ("default_sets", "default_reps", "default_duration_seconds")}),
        ("Injury Considerations", {"fields": ("high_impact", "joint_stress")}),
    )

    readonly_fields = ["created_at", "updated_at"]


@admin.register(ExerciseType)
class ExerciseTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "description"]
    search_fields = ["name"]


@admin.register(MuscleGroup)
class MuscleGroupAdmin(admin.ModelAdmin):
    list_display = ["name", "description"]
    search_fields = ["name"]


@admin.register(Muscle)
class MuscleAdmin(admin.ModelAdmin):
    list_display = ["name", "muscle_group", "description"]
    search_fields = ["name", "muscle_group__name"]
    list_filter = ["muscle_group"]
    ordering = ["muscle_group", "name"]


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ["name", "description"]
    search_fields = ["name"]


@admin.register(UserInjury)
class UserInjuryAdmin(admin.ModelAdmin):
    list_display = ["user", "muscle", "severity", "start_date", "end_date", "is_active"]
    search_fields = ["user__email", "muscle__name"]
    list_filter = ["severity", "is_active", "start_date"]
    date_hierarchy = "start_date"
    readonly_fields = ["created_at"]


@admin.register(UserEquipmentProfile)
class UserEquipmentProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "location"]
    search_fields = ["user__email"]
    list_filter = ["location"]
    filter_horizontal = ["equipment"]
