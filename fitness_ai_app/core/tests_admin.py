from django.contrib import admin
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse

from core.models import Equipment, ExerciseType, Muscle, MuscleGroup, TrainingExercise


class AdminExerciseDatabaseVisibilityTests(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="adminuser",
            email="admin@example.com",
            password="adminpass123",
        )
        self.client.force_login(self.superuser)

    def test_exercise_database_models_are_registered(self):
        self.assertIn(TrainingExercise, admin.site._registry)
        self.assertIn(ExerciseType, admin.site._registry)
        self.assertIn(MuscleGroup, admin.site._registry)
        self.assertIn(Muscle, admin.site._registry)
        self.assertIn(Equipment, admin.site._registry)

    def test_admin_index_shows_exercise_database_section(self):
        response = self.client.get(reverse("admin:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Core / Exercise Database")
        self.assertContains(response, reverse("admin:core_trainingexercise_changelist"))

    def test_grouped_app_list_contains_exercise_database_models(self):
        request = RequestFactory().get("/admin/")
        request.user = self.superuser

        app_list = admin.site.get_app_list(request)
        section = next(app for app in app_list if app["app_label"] == "core_exercise_database")
        model_names = {model["object_name"] for model in section["models"]}

        self.assertEqual(
            model_names,
            {"TrainingExercise", "ExerciseType", "MuscleGroup", "Muscle", "Equipment"},
        )
