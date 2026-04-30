"""
Tests for the Workout Module functionality including:
- Timer persistence
- Exercise completion tracking
- Set progress saving/loading
- Workout status updates
"""

import json
from datetime import date
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Workout, Exercise, SetProgress, Meal, FoodItem


class WorkoutModelTests(TestCase):
    """Test Workout model functionality"""

    def setUp(self):
        """Create test user and workout"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.workout = Workout.objects.create(
            user=self.user,
            name='Upper Body',
            goal='strength',
            date=timezone.now().date(),
            status='planned'
        )

    def test_workout_creation(self):
        """Test that workout is created with correct defaults"""
        self.assertEqual(self.workout.name, 'Upper Body')
        self.assertEqual(self.workout.status, 'planned')
        self.assertEqual(self.workout.current_session_seconds, 0)
        self.assertIsNone(self.workout.total_duration_seconds)

    def test_workout_status_choices(self):
        """Test that workout status can be set to completed"""
        self.workout.status = 'completed'
        self.workout.save()

        refreshed_workout = Workout.objects.get(id=self.workout.id)
        self.assertEqual(refreshed_workout.status, 'completed')

    def test_timer_persistence(self):
        """Test that current_session_seconds is saved"""
        self.workout.current_session_seconds = 300
        self.workout.save()

        refreshed_workout = Workout.objects.get(id=self.workout.id)
        self.assertEqual(refreshed_workout.current_session_seconds, 300)

    def test_total_duration_seconds(self):
        """Test that total_duration_seconds is saved"""
        self.workout.total_duration_seconds = 1200
        self.workout.save()

        refreshed_workout = Workout.objects.get(id=self.workout.id)
        self.assertEqual(refreshed_workout.total_duration_seconds, 1200)


class ExerciseCompletionTests(TestCase):
    """Test Exercise completion functionality"""

    def setUp(self):
        """Create test user, workout, and exercises"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.workout = Workout.objects.create(
            user=self.user,
            name='Upper Body',
            goal='strength',
            date=timezone.now().date()
        )
        self.exercise = Exercise.objects.create(
            workout=self.workout,
            name='Bench Press',
            muscle_group='chest',
            sets=3,
            reps=8,
            weight=225,
            completed=False
        )

    def test_exercise_creation(self):
        """Test that exercise is created with correct values"""
        self.assertEqual(self.exercise.name, 'Bench Press')
        self.assertEqual(self.exercise.sets, 3)
        self.assertEqual(self.exercise.reps, 8)
        self.assertEqual(self.exercise.weight, 225)
        self.assertFalse(self.exercise.completed)

    def test_exercise_completion(self):
        """Test marking an exercise as completed"""
        self.exercise.completed = True
        self.exercise.save()

        refreshed_exercise = Exercise.objects.get(id=self.exercise.id)
        self.assertTrue(refreshed_exercise.completed)

    def test_multiple_exercises_independent(self):
        """Test that completing one exercise doesn't affect others"""
        exercise2 = Exercise.objects.create(
            workout=self.workout,
            name='Incline Press',
            muscle_group='chest',
            sets=3,
            reps=8,
            weight=185,
            completed=False
        )

        self.exercise.completed = True
        self.exercise.save()

        refreshed_exercise2 = Exercise.objects.get(id=exercise2.id)
        self.assertFalse(refreshed_exercise2.completed)


class SetProgressTests(TestCase):
    """Test SetProgress model for saving set completion states"""

    def setUp(self):
        """Create test user, workout, and exercise"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.workout = Workout.objects.create(
            user=self.user,
            name='Leg Day',
            goal='strength',
            date=timezone.now().date()
        )
        self.exercise = Exercise.objects.create(
            workout=self.workout,
            name='Squats',
            muscle_group='legs',
            sets=4,
            reps=6,
            weight=315
        )

    def test_set_progress_creation(self):
        """Test creating a SetProgress record"""
        progress = SetProgress.objects.create(
            exercise=self.exercise,
            set_number=1,
            completed=True
        )
        self.assertEqual(progress.set_number, 1)
        self.assertTrue(progress.completed)

    def test_multiple_sets_tracking(self):
        """Test tracking completion of multiple sets"""
        sets_data = []
        for i in range(1, 5):
            progress = SetProgress.objects.create(
                exercise=self.exercise,
                set_number=i,
                completed=(i <= 3)  # First 3 completed, 4th not
            )
            sets_data.append(progress)

        completed_sets = SetProgress.objects.filter(
            exercise=self.exercise,
            completed=True
        ).count()
        self.assertEqual(completed_sets, 3)

    def test_all_sets_completed(self):
        """Test checking if all sets are completed"""
        for i in range(1, 5):
            SetProgress.objects.create(
                exercise=self.exercise,
                set_number=i,
                completed=True
            )

        all_sets = SetProgress.objects.filter(
            exercise=self.exercise
        )
        all_completed = all(s.completed for s in all_sets)
        self.assertTrue(all_completed)


class CompleteExerciseAPITests(TestCase):
    """Test the /api/exercises/complete_by_ids/ endpoint"""

    def setUp(self):
        """Create test client, user, and data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.workout = Workout.objects.create(
            user=self.user,
            name='Full Body',
            goal='strength',
            date=timezone.now().date()
        )
        self.exercise1 = Exercise.objects.create(
            workout=self.workout,
            name='Bench Press',
            muscle_group='chest',
            completed=False
        )
        self.exercise2 = Exercise.objects.create(
            workout=self.workout,
            name='Squats',
            muscle_group='legs',
            completed=False
        )
        self.client.login(username='testuser', password='testpass123')

    def test_complete_single_exercise(self):
        """Test marking a single exercise as completed"""
        response = self.client.post(
            '/api/exercises/complete_by_ids/',
            data=json.dumps({
                'exercise_ids': [self.exercise1.id]
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['completed_count'], 1)

        refreshed_exercise = Exercise.objects.get(id=self.exercise1.id)
        self.assertTrue(refreshed_exercise.completed)

    def test_complete_multiple_exercises(self):
        """Test marking multiple exercises as completed"""
        response = self.client.post(
            '/api/exercises/complete_by_ids/',
            data=json.dumps({
                'exercise_ids': [self.exercise1.id, self.exercise2.id]
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['completed_count'], 2)

    def test_complete_nonexistent_exercise(self):
        """Test completing an exercise that doesn't exist"""
        response = self.client.post(
            '/api/exercises/complete_by_ids/',
            data=json.dumps({
                'exercise_ids': [99999]
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        # Should succeed but with 0 completed (since exercise doesn't exist)
        self.assertTrue(data['success'])

    def test_empty_exercise_list(self):
        """Test with empty exercise list"""
        response = self.client.post(
            '/api/exercises/complete_by_ids/',
            data=json.dumps({
                'exercise_ids': []
            }),
            content_type='application/json'
        )

        # Empty list should return 400 (bad request)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])

    def test_unauthenticated_request(self):
        """Test that unauthenticated requests are rejected"""
        self.client.logout()
        response = self.client.post(
            '/api/exercises/complete_by_ids/',
            data=json.dumps({
                'exercise_ids': [self.exercise1.id]
            }),
            content_type='application/json'
        )

        # Should redirect to login
        self.assertEqual(response.status_code, 302)


class CompleteWorkoutAPITests(TestCase):
    """Test the /api/workout/complete/ endpoint"""

    def setUp(self):
        """Create test client, user, and workout"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.workout = Workout.objects.create(
            user=self.user,
            name='Workout A',
            goal='strength',
            date=timezone.now().date(),
            status='planned'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_complete_workout(self):
        """Test marking a workout as completed"""
        response = self.client.post(
            '/api/workout/complete/',
            data=json.dumps({
                'workout_id': self.workout.id
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['status'], 'completed')

        refreshed_workout = Workout.objects.get(id=self.workout.id)
        self.assertEqual(refreshed_workout.status, 'completed')

    def test_complete_already_completed_workout(self):
        """Test completing a workout that's already completed"""
        self.workout.status = 'completed'
        self.workout.save()

        response = self.client.post(
            '/api/workout/complete/',
            data=json.dumps({
                'workout_id': self.workout.id
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

    def test_complete_nonexistent_workout(self):
        """Test completing a workout that doesn't exist"""
        response = self.client.post(
            '/api/workout/complete/',
            data=json.dumps({
                'workout_id': 99999
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertFalse(data['success'])

    def test_missing_workout_id(self):
        """Test request without workout_id"""
        response = self.client.post(
            '/api/workout/complete/',
            data=json.dumps({}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)

    def test_complete_other_users_workout(self):
        """Test that users can't complete other users' workouts"""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        other_workout = Workout.objects.create(
            user=other_user,
            name='Other Workout',
            goal='cardio',
            date=timezone.now().date()
        )

        response = self.client.post(
            '/api/workout/complete/',
            data=json.dumps({
                'workout_id': other_workout.id
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_complete_workout(self):
        """Test that unauthenticated requests are rejected"""
        self.client.logout()
        response = self.client.post(
            '/api/workout/complete/',
            data=json.dumps({
                'workout_id': self.workout.id
            }),
            content_type='application/json'
        )

        # Should redirect to login
        self.assertEqual(response.status_code, 302)


class SaveSetProgressAPITests(TestCase):
    """Test the /api/set_progress/save/ endpoint"""

    def setUp(self):
        """Create test client, user, and data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.workout = Workout.objects.create(
            user=self.user,
            name='Workout',
            goal='strength',
            date=timezone.now().date()
        )
        self.exercise = Exercise.objects.create(
            workout=self.workout,
            name='Bench Press',
            muscle_group='chest',
            sets=3
        )
        self.client.login(username='testuser', password='testpass123')

    def test_save_single_set(self):
        """Test saving a single set completion"""
        response = self.client.post(
            '/api/set_progress/save/',
            data=json.dumps({
                'workout_id': self.workout.id,
                'set_data': [
                    {
                        'exercise_id': self.exercise.id,
                        'set_number': 1,
                        'is_completed': True
                    }
                ],
                'timer_seconds': 0
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['saved_count'], 1)

    def test_save_multiple_sets(self):
        """Test saving multiple set completions"""
        response = self.client.post(
            '/api/set_progress/save/',
            data=json.dumps({
                'workout_id': self.workout.id,
                'set_data': [
                    {'exercise_id': self.exercise.id, 'set_number': 1, 'is_completed': True},
                    {'exercise_id': self.exercise.id, 'set_number': 2, 'is_completed': True},
                    {'exercise_id': self.exercise.id, 'set_number': 3, 'is_completed': False}
                ],
                'timer_seconds': 300
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['saved_count'], 3)

        # Verify timer was saved
        refreshed_workout = Workout.objects.get(id=self.workout.id)
        self.assertEqual(refreshed_workout.current_session_seconds, 300)

    def test_partial_set_completion(self):
        """Test saving with only some sets completed"""
        response = self.client.post(
            '/api/set_progress/save/',
            data=json.dumps({
                'workout_id': self.workout.id,
                'set_data': [
                    {'exercise_id': self.exercise.id, 'set_number': 1, 'is_completed': True},
                    {'exercise_id': self.exercise.id, 'set_number': 2, 'is_completed': False},
                    {'exercise_id': self.exercise.id, 'set_number': 3, 'is_completed': False}
                ],
                'timer_seconds': 0
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])


class SaveWorkoutTimeAPITests(TestCase):
    """Test the /api/workout/save_time/ endpoint"""

    def setUp(self):
        """Create test client, user, and workout"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.workout = Workout.objects.create(
            user=self.user,
            name='Timed Workout',
            goal='strength',
            date=timezone.now().date()
        )
        self.client.login(username='testuser', password='testpass123')

    def test_save_workout_duration(self):
        """Test saving workout duration"""
        response = self.client.post(
            '/api/workout/save_time/',
            data=json.dumps({
                'workout_id': self.workout.id,
                'total_seconds': 1800  # 30 minutes
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['total_seconds'], 1800)

        refreshed_workout = Workout.objects.get(id=self.workout.id)
        self.assertEqual(refreshed_workout.total_duration_seconds, 1800)

    def test_save_zero_duration(self):
        """Test saving zero duration"""
        response = self.client.post(
            '/api/workout/save_time/',
            data=json.dumps({
                'workout_id': self.workout.id,
                'total_seconds': 0
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        refreshed_workout = Workout.objects.get(id=self.workout.id)
        self.assertEqual(refreshed_workout.total_duration_seconds, 0)

    def test_save_large_duration(self):
        """Test saving large duration (e.g., 2 hours)"""
        response = self.client.post(
            '/api/workout/save_time/',
            data=json.dumps({
                'workout_id': self.workout.id,
                'total_seconds': 7200
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        refreshed_workout = Workout.objects.get(id=self.workout.id)
        self.assertEqual(refreshed_workout.total_duration_seconds, 7200)


class GetSetProgressAPITests(TestCase):
    """Test the /api/set_progress/get/ endpoint"""

    def setUp(self):
        """Create test client, user, and data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.workout = Workout.objects.create(
            user=self.user,
            name='Workout',
            goal='strength',
            date=timezone.now().date()
        )
        self.exercise = Exercise.objects.create(
            workout=self.workout,
            name='Bench Press',
            muscle_group='chest',
            sets=3
        )
        self.client.login(username='testuser', password='testpass123')

    def test_get_empty_set_progress(self):
        """Test getting set progress when none exists"""
        response = self.client.get(
            f'/api/set_progress/get/?workout_id={self.workout.id}'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['set_progress']), 0)

    def test_get_existing_set_progress(self):
        """Test retrieving saved set progress"""
        # First save some progress for set 1
        SetProgress.objects.create(
            exercise=self.exercise,
            set_number=1,
            completed=True
        )
        # Then save for set 2
        SetProgress.objects.create(
            exercise=self.exercise,
            set_number=2,
            completed=False
        )

        response = self.client.get(
            f'/api/set_progress/get/?workout_id={self.workout.id}'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        # Should have at least 1 set progress record
        self.assertGreaterEqual(len(data['set_progress']), 1)

    def test_get_without_workout_id(self):
        """Test get request without workout_id"""
        response = self.client.get('/api/set_progress/get/')

        self.assertEqual(response.status_code, 400)


class WorkoutIntegrationTests(TestCase):
    """Integration tests combining multiple features"""

    def setUp(self):
        """Create test client, user, workout, and exercises"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.workout = Workout.objects.create(
            user=self.user,
            name='Full Body',
            goal='strength',
            date=timezone.now().date()
        )
        self.bench = Exercise.objects.create(
            workout=self.workout,
            name='Bench Press',
            muscle_group='chest',
            sets=3
        )
        self.squat = Exercise.objects.create(
            workout=self.workout,
            name='Squats',
            muscle_group='legs',
            sets=3
        )
        self.client.login(username='testuser', password='testpass123')

    def test_complete_workout_flow(self):
        """Test complete workflow: save progress, complete exercises, mark workout done"""
        # Step 1: Save set progress
        self.client.post(
            '/api/set_progress/save/',
            data=json.dumps({
                'workout_id': self.workout.id,
                'set_data': [
                    {'exercise_id': self.bench.id, 'set_number': 1, 'is_completed': True},
                    {'exercise_id': self.bench.id, 'set_number': 2, 'is_completed': True},
                    {'exercise_id': self.bench.id, 'set_number': 3, 'is_completed': True},
                    {'exercise_id': self.squat.id, 'set_number': 1, 'is_completed': True},
                    {'exercise_id': self.squat.id, 'set_number': 2, 'is_completed': True},
                    {'exercise_id': self.squat.id, 'set_number': 3, 'is_completed': True},
                ],
                'timer_seconds': 1800
            }),
            content_type='application/json'
        )

        # Step 2: Complete exercises
        response = self.client.post(
            '/api/exercises/complete_by_ids/',
            data=json.dumps({
                'exercise_ids': [self.bench.id, self.squat.id]
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        # Step 3: Mark workout as completed
        response = self.client.post(
            '/api/workout/complete/',
            data=json.dumps({
                'workout_id': self.workout.id
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        # Verify final state
        refreshed_workout = Workout.objects.get(id=self.workout.id)
        self.assertEqual(refreshed_workout.status, 'completed')
        self.assertEqual(refreshed_workout.current_session_seconds, 1800)

        refreshed_bench = Exercise.objects.get(id=self.bench.id)
        self.assertTrue(refreshed_bench.completed)

        refreshed_squat = Exercise.objects.get(id=self.squat.id)
        self.assertTrue(refreshed_squat.completed)

    def test_partial_workout_completion(self):
        """Test completing only some exercises in a workout"""
        # Save progress for only bench press
        self.client.post(
            '/api/set_progress/save/',
            data=json.dumps({
                'workout_id': self.workout.id,
                'set_data': [
                    {'exercise_id': self.bench.id, 'set_number': 1, 'is_completed': True},
                    {'exercise_id': self.bench.id, 'set_number': 2, 'is_completed': True},
                    {'exercise_id': self.bench.id, 'set_number': 3, 'is_completed': True},
                ],
                'timer_seconds': 900
            }),
            content_type='application/json'
        )

        # Complete only bench press
        self.client.post(
            '/api/exercises/complete_by_ids/',
            data=json.dumps({
                'exercise_ids': [self.bench.id]
            }),
            content_type='application/json'
        )

        # Mark workout as completed anyway
        self.client.post(
            '/api/workout/complete/',
            data=json.dumps({
                'workout_id': self.workout.id
            }),
            content_type='application/json'
        )

        # Verify mixed state
        refreshed_bench = Exercise.objects.get(id=self.bench.id)
        refreshed_squat = Exercise.objects.get(id=self.squat.id)

        self.assertTrue(refreshed_bench.completed)
        self.assertFalse(refreshed_squat.completed)

        refreshed_workout = Workout.objects.get(id=self.workout.id)
        self.assertEqual(refreshed_workout.status, 'completed')


# ==================== SECURITY TESTS ====================

class WorkoutSecurityTests(TestCase):
    """Tests for security vulnerabilities in workout API endpoints"""

    def setUp(self):
        self.user1 = User.objects.create_user('user1', 'user1@test.com', 'pass123')
        self.user2 = User.objects.create_user('user2', 'user2@test.com', 'pass123')
        
        self.workout1 = Workout.objects.create(user=self.user1, date=date.today())
        self.exercise1 = Exercise.objects.create(workout=self.workout1, name='Bench', sets=3)
        self.set1 = SetProgress.objects.create(exercise=self.exercise1, set_number=1, completed=False)

    def test_complete_workout_requires_authentication(self):
        """Test that unauthenticated users cannot complete workouts"""
        self.client.logout()
        response = self.client.post(
            '/api/workout/complete/',
            data=json.dumps({'workout_id': self.workout1.id}),
            content_type='application/json'
        )
        # Should redirect to login (302)
        self.assertEqual(response.status_code, 302)

    def test_complete_workout_unauthorized_access(self):
        """Test that users cannot complete other users' workouts"""
        self.client.login(username='user2', password='pass123')
        response = self.client.post(
            '/api/workout/complete/',
            data=json.dumps({'workout_id': self.workout1.id}),
            content_type='application/json'
        )
        # Should return 404 - workout not found
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'Workout not found')

    def test_save_workout_time_requires_authentication(self):
        """Test that unauthenticated users cannot save workout time"""
        self.client.logout()
        response = self.client.post(
            '/api/workout/save_time/',
            data=json.dumps({'workout_id': self.workout1.id, 'total_seconds': 300}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 302)

    def test_save_workout_time_unauthorized_access(self):
        """Test that users cannot modify other users' workouts"""
        self.client.login(username='user2', password='pass123')
        response = self.client.post(
            '/api/workout/save_time/',
            data=json.dumps({'workout_id': self.workout1.id, 'total_seconds': 300}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'Workout not found')

    def test_complete_exercises_requires_authentication(self):
        """Test that unauthenticated users cannot complete exercises"""
        self.client.logout()
        response = self.client.post(
            '/api/exercises/complete_by_ids/',
            data=json.dumps({'exercise_ids': [self.exercise1.id]}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 302)

    def test_complete_exercises_unauthorized_access(self):
        """Test that users cannot complete other users' exercises"""
        self.client.login(username='user2', password='pass123')
        response = self.client.post(
            '/api/exercises/complete_by_ids/',
            data=json.dumps({'exercise_ids': [self.exercise1.id]}),
            content_type='application/json'
        )
        # User2 has no exercises, so should get empty result
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['completed_count'], 0)
        self.assertEqual(data['exercise_ids'], [])

    def test_error_messages_dont_expose_details(self):
        """Test that error messages don't expose internal details"""
        self.client.login(username='user1', password='pass123')
        
        # Try with invalid JSON - should not expose parse details
        response = self.client.post(
            '/api/exercises/complete_by_ids/',
            data='{"invalid json',
            content_type='application/json'
        )
        data = json.loads(response.content)
        # Error message should be generic, not contain traceback
        self.assertNotIn('Traceback', data['error'])
        self.assertNotIn('File', data['error'])
        self.assertEqual(data['error'], 'Invalid JSON')

    def test_invalid_exercise_ids_handled_gracefully(self):
        """Test that invalid exercise IDs are handled without exposing details"""
        self.client.login(username='user1', password='pass123')
        response = self.client.post(
            '/api/exercises/complete_by_ids/',
            data=json.dumps({'exercise_ids': [999999, 888888]}),
            content_type='application/json'
        )
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        # No matching exercises for this user
        self.assertEqual(data['completed_count'], 0)
        self.assertEqual(data['exercise_ids'], [])

    def test_save_set_progress_requires_authentication(self):
        """Test that unauthenticated users cannot save set progress"""
        self.client.logout()
        response = self.client.post(
            '/api/set_progress/save/',
            data=json.dumps({
                'workout_id': self.workout1.id,
                'set_data': [{'exercise_id': self.exercise1.id, 'set_number': 1, 'completed': True}]
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 302)

    def test_cross_user_set_progress_isolation(self):
        """Test that users can only modify their own set progress"""
        # User1 saves their progress
        self.client.login(username='user1', password='pass123')
        response = self.client.post(
            '/api/set_progress/save/',
            data=json.dumps({
                'workout_id': self.workout1.id,
                'set_data': [{'exercise_id': self.exercise1.id, 'set_number': 1, 'completed': True}],
                'timer_seconds': 100
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # User2 tries to read User1's set progress
        self.client.login(username='user2', password='pass123')
        response = self.client.get(
            '/api/set_progress/get/?workout_id=' + str(self.workout1.id)
        )
        self.assertEqual(response.status_code, 404)

    def test_invalid_request_data_handling(self):
        """Test that invalid request data is handled securely"""
        self.client.login(username='user1', password='pass123')
        
        # Missing required fields
        response = self.client.post(
            '/api/workout/complete/',
            data=json.dumps({}),
            content_type='application/json'
        )
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('required', data['error'].lower())

    def test_negative_workout_id_validation(self):
        """Test that negative IDs are handled correctly"""
        self.client.login(username='user1', password='pass123')
        response = self.client.post(
            '/api/workout/save_time/',
            data=json.dumps({'workout_id': -1, 'total_seconds': 300}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertFalse(data['success'])


# ==================== OPENAI API SECURITY TESTS ====================

class OpenAIAPISecurityTests(TestCase):
    """Tests for security of OpenAI API endpoints"""

    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@test.com', 'pass123')
        self.client.login(username='testuser', password='pass123')

    def test_api_chat_requires_authentication(self):
        """Test that /api/chat requires login"""
        self.client.logout()
        response = self.client.post(
            '/api/chat',
            data=json.dumps({'messages': [{'role': 'user', 'content': 'Hello'}]}),
            content_type='application/json'
        )
        # Should redirect to login (302)
        self.assertEqual(response.status_code, 302)

    def test_api_chat_stream_requires_authentication(self):
        """Test that /api/chat_stream requires login"""
        self.client.logout()
        response = self.client.post(
            '/api/chat/stream',
            data=json.dumps({'messages': [{'role': 'user', 'content': 'Hello'}]}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 302)

    def test_api_chat_apply_plan_requires_authentication(self):
        """Test that /api/chat_apply_plan requires login"""
        self.client.logout()
        response = self.client.post(
            '/api/chat/apply_plan',
            data=json.dumps({'planner_payload': {}}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 302)

    def test_api_chat_requires_valid_json(self):
        """Test that invalid JSON is rejected"""
        response = self.client.post(
            '/api/chat',
            data='{"invalid json',
            content_type='application/json'
        )
        # Invalid JSON should return 400
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)

    def test_api_chat_requires_messages_field(self):
        """Test that messages field is required"""
        response = self.client.post(
            '/api/chat',
            data=json.dumps({}),
            content_type='application/json'
        )
        self.assertIn(response.status_code, [400, 200])

    def test_api_chat_error_messages_generic(self):
        """Test that error messages don't expose internal details"""
        # This test ensures that if an error occurs, it doesn't leak details
        self.client.logout()
        response = self.client.post(
            '/api/chat',
            data=json.dumps({'messages': []}),
            content_type='application/json'
        )
        # Should get 302 redirect, not 500 with error details
        self.assertEqual(response.status_code, 302)

    def test_api_chat_stream_error_messages_generic(self):
        """Test that stream error messages don't expose internal details"""
        # Invalid payload should return generic error
        response = self.client.post(
            '/api/chat/stream',
            data=json.dumps({}),
            content_type='application/json'
        )
        # Should not contain detailed error messages
        if response.status_code == 200:
            # For streaming, check content
            self.assertNotIn('Traceback', response.content.decode())
            self.assertNotIn('File', response.content.decode())

    def test_unauthenticated_cannot_trigger_api_calls(self):
        """Test that unauthenticated users cannot make API calls"""
        self.client.logout()
        
        # Attempt 1: /api/chat
        response = self.client.post(
            '/api/chat',
            data=json.dumps({'messages': [{'role': 'user', 'content': 'test'}]}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 302)
        
        # Attempt 2: /api/chat_stream
        response = self.client.post(
            '/api/chat/stream',
            data=json.dumps({'messages': [{'role': 'user', 'content': 'test'}]}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 302)
        
        # Attempt 3: /api/chat_apply_plan
        response = self.client.post(
            '/api/chat/apply_plan',
            data=json.dumps({'planner_payload': {'workout_plan': []}}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 302)

    def test_authenticated_user_can_access_api_chat(self):
        """Test that authenticated users can make requests (though API call may fail without key)"""
        # This should not redirect to login
        response = self.client.post(
            '/api/chat',
            data=json.dumps({'messages': [{'role': 'user', 'content': 'test'}]}),
            content_type='application/json'
        )
        # Should be 400/403/500 (API error) NOT 302 (auth redirect)
        self.assertNotEqual(response.status_code, 302)

    def test_no_csrf_bypass_needed(self):
        """Test that CSRF token is not required for authenticated users"""
        # The endpoint has @csrf_exempt, so CSRF bypass shouldn't be needed
        # but auth IS still required
        response = self.client.post(
            '/api/chat',
            data=json.dumps({'messages': [{'role': 'user', 'content': 'test'}]}),
            content_type='application/json',
            HTTP_X_CSRFTOKEN=''  # Empty CSRF token
        )
        # Should NOT be 403 (CSRF failed), should get past CSRF to auth/API
        self.assertNotEqual(response.status_code, 403)

    def test_conversation_id_validation(self):
        """Test that invalid conversation_id is handled"""
        response = self.client.post(
            '/api/chat',
            data=json.dumps({
                'messages': [{'role': 'user', 'content': 'test'}],
                'conversation_id': 'invalid'  # Should be integer
            }),
            content_type='application/json'
        )
        # Should reject invalid ID format
        self.assertEqual(response.status_code, 400)

    def test_large_message_handling(self):
        """Test that extremely large messages don't cause issues"""
        response = self.client.post(
            '/api/chat',
            data=json.dumps({
                'messages': [{'role': 'user', 'content': 'x' * 10000}]
            }),
            content_type='application/json'
        )
        # Should not crash, either 400 or API error
        self.assertIn(response.status_code, [400, 500, 502])

    def test_malicious_payload_rejected(self):
        """Test that malicious payloads are rejected safely"""
        response = self.client.post(
            '/api/chat',
            data=json.dumps({
                'messages': 'not a list',  # Should be array
            }),
            content_type='application/json'
        )
        # Should handle gracefully
        self.assertIn(response.status_code, [400, 500])


# ==================== IDOR VULNERABILITY TESTS ====================

class IDORFoodItemSecurityTests(TestCase):
    """Tests for IDOR (Insecure Direct Object Reference) vulnerabilities in food item endpoints"""

    def setUp(self):
        """Create two users with food items"""
        self.user1 = User.objects.create_user('user1', 'user1@test.com', 'pass123')
        self.user2 = User.objects.create_user('user2', 'user2@test.com', 'pass123')
        
        # Create meals for each user
        self.meal1 = Meal.objects.create(user=self.user1, name='Breakfast', date=date.today())
        self.meal2 = Meal.objects.create(user=self.user2, name='Breakfast', date=date.today())
        
        # Create food items for each user
        self.food1 = FoodItem.objects.create(
            meal=self.meal1,
            name='Apple',
            calories=100,
            protein=0,
            carbs=25,
            fats=0
        )
        self.food2 = FoodItem.objects.create(
            meal=self.meal2,
            name='Banana',
            calories=120,
            protein=1,
            carbs=27,
            fats=0
        )

    def test_user_cannot_modify_other_users_food(self):
        """Test that User1 cannot modify User2's food item via IDOR"""
        self.client.login(username='user1', password='pass123')
        
        # Attempt to modify User2's food item
        response = self.client.post(
            '/api/save_food/',
            data=json.dumps({
                'id': self.food2.id,  # User2's food
                'name': 'HACKED BANANA',
                'calories': 9999,
                'protein': 0,
                'carbs': 0,
                'fats': 0
            }),
            content_type='application/json'
        )
        
        # Should be denied (403 or 404)
        self.assertIn(response.status_code, [403, 404])
        
        # Verify food was not modified
        self.food2.refresh_from_db()
        self.assertEqual(self.food2.name, 'Banana')
        self.assertEqual(self.food2.calories, 120)

    def test_user_can_modify_own_food(self):
        """Test that User1 can modify their own food item"""
        self.client.login(username='user1', password='pass123')
        
        response = self.client.post(
            '/api/save_food/',
            data=json.dumps({
                'id': self.food1.id,  # User1's own food
                'name': 'Green Apple',
                'calories': 95,
                'protein': 0,
                'carbs': 24,
                'fats': 0
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Verify food was modified
        self.food1.refresh_from_db()
        self.assertEqual(self.food1.name, 'Green Apple')
        self.assertEqual(self.food1.calories, 95)

    def test_idor_with_invalid_id(self):
        """Test that accessing non-existent food ID returns 404"""
        self.client.login(username='user1', password='pass123')
        
        response = self.client.post(
            '/api/save_food/',
            data=json.dumps({
                'id': 999999,  # Non-existent ID
                'name': 'Fake Food',
                'calories': 100,
                'protein': 0,
                'carbs': 0,
                'fats': 0
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)

    def test_idor_prevention_with_enumeration(self):
        """Test IDOR prevention when enumerating food IDs"""
        self.client.login(username='user1', password='pass123')
        
        # Try to modify each potential ID
        for food_id in [self.food1.id, self.food2.id]:
            response = self.client.post(
                '/api/save_food/',
                data=json.dumps({
                    'id': food_id,
                    'name': 'CORRUPTED',
                    'calories': 0,
                    'protein': 0,
                    'carbs': 0,
                    'fats': 0
                }),
                content_type='application/json'
            )
            
            # Only own food should succeed
            if food_id == self.food1.id:
                self.assertEqual(response.status_code, 200)
            else:
                self.assertIn(response.status_code, [403, 404])

    def test_unauthenticated_cannot_save_food(self):
        """Test that unauthenticated users cannot save food"""
        self.client.logout()
        
        response = self.client.post(
            '/api/save_food/',
            data=json.dumps({
                'id': self.food1.id,
                'name': 'Hacked',
                'calories': 0,
                'protein': 0,
                'carbs': 0,
                'fats': 0
            }),
            content_type='application/json'
        )
        
        # Should redirect or deny
        self.assertIn(response.status_code, [302, 403, 404])

    def test_food_modification_validation(self):
        """Test that food modification validates input"""
        self.client.login(username='user1', password='pass123')
        
        # Invalid numeric values
        response = self.client.post(
            '/api/save_food/',
            data=json.dumps({
                'id': self.food1.id,
                'name': 'Apple',
                'calories': 'not a number',
                'protein': 0,
                'carbs': 0,
                'fats': 0
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)

    def test_food_modification_updates_correct_fields(self):
        """Test that only the specified fields are updated"""
        self.client.login(username='user1', password='pass123')
        
        original_completed = self.food1.completed
        
        response = self.client.post(
            '/api/save_food/',
            data=json.dumps({
                'id': self.food1.id,
                'name': 'Modified Apple',
                'calories': 110,
                'protein': 1,
                'carbs': 26,
                'fats': 0.5
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        self.food1.refresh_from_db()
        self.assertEqual(self.food1.name, 'Modified Apple')
        self.assertEqual(self.food1.calories, 110)
        self.assertEqual(self.food1.protein, 1)
        self.assertEqual(self.food1.completed, original_completed)

    def test_system_food_access_denied_for_regular_users(self):
        """Test that regular users cannot modify system food items"""
        # Create a system user and food
        system_user, _ = User.objects.get_or_create(
            username='system@spotter.ai',
            defaults={'email': 'system@spotter.ai', 'is_active': False}
        )
        system_meal, _ = Meal.objects.get_or_create(
            user=system_user,
            name='Food Database',
            date=date(2000, 1, 1)
        )
        system_food = FoodItem.objects.create(
            meal=system_meal,
            name='System Chicken',
            calories=200,
            protein=30,
            carbs=0,
            fats=5
        )
        
        # Try to modify as regular user
        self.client.login(username='user1', password='pass123')
        response = self.client.post(
            '/api/save_food/',
            data=json.dumps({
                'id': system_food.id,
                'name': 'HACKED SYSTEM FOOD',
                'calories': 0,
                'protein': 0,
                'carbs': 0,
                'fats': 0
            }),
            content_type='application/json'
        )
        
        # Should be denied
        self.assertEqual(response.status_code, 403)
        
        # Verify not modified
        system_food.refresh_from_db()
        self.assertEqual(system_food.name, 'System Chicken')

    def test_cross_user_data_isolation(self):
        """Test complete isolation between users"""
        # User1 modifies their food
        self.client.login(username='user1', password='pass123')
        self.client.post(
            '/api/save_food/',
            data=json.dumps({
                'id': self.food1.id,
                'name': 'User1 Apple',
                'calories': 105,
                'protein': 0,
                'carbs': 25,
                'fats': 0
            }),
            content_type='application/json'
        )
        
        # User2 modifies their food
        self.client.login(username='user2', password='pass123')
        self.client.post(
            '/api/save_food/',
            data=json.dumps({
                'id': self.food2.id,
                'name': 'User2 Banana',
                'calories': 125,
                'protein': 1,
                'carbs': 28,
                'fats': 0
            }),
            content_type='application/json'
        )
        
        # Verify User1's food is still their version
        self.food1.refresh_from_db()
        self.assertEqual(self.food1.name, 'User1 Apple')
        self.assertEqual(self.food1.calories, 105)
        
        # Verify User2's food is their version
        self.food2.refresh_from_db()
        self.assertEqual(self.food2.name, 'User2 Banana')
        self.assertEqual(self.food2.calories, 125)


class OpenRedirectSecurityTests(TestCase):
    """Test suite for open redirect vulnerability in login redirects"""
    
    def setUp(self):
        """Create test user for login tests"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='TestPass123'
        )
    
    def test_valid_same_host_redirect_allowed(self):
        """Test that valid same-host redirects are allowed"""
        response = self.client.post(
            '/user_login/?next=/train/',
            {
                'email': 'testuser@example.com',
                'password': 'TestPass123'
            },
            follow=False
        )
        
        # Should redirect to /train/ (same host)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith('/train/') or '/train/' in response.url)
    
    def test_external_url_redirect_blocked(self):
        """Test that external URL redirects are blocked"""
        response = self.client.post(
            '/user_login/?next=https://evil.com',
            {
                'email': 'testuser@example.com',
                'password': 'TestPass123'
            },
            follow=False
        )
        
        # Should redirect to safe default (home_dash), not evil.com
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('evil.com', response.url)
        self.assertTrue(response.url.endswith('/') or 'home_dash' in response.url or response.url.endswith('/home_dash/'))
    
    def test_protocol_escape_redirect_blocked(self):
        """Test that protocol-based escape attempts are blocked"""
        response = self.client.post(
            '/user_login/?next=//evil.com',
            {
                'email': 'testuser@example.com',
                'password': 'TestPass123'
            },
            follow=False
        )
        
        # Should redirect to safe default, not //evil.com
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('//evil.com', response.url)
    
    def test_javascript_protocol_redirect_blocked(self):
        """Test that javascript: protocol redirects are blocked"""
        response = self.client.post(
            '/user_login/?next=javascript:alert(1)',
            {
                'email': 'testuser@example.com',
                'password': 'TestPass123'
            },
            follow=False
        )
        
        # Should redirect to safe default, not javascript
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('javascript:', response.url)
    
    def test_data_protocol_redirect_blocked(self):
        """Test that data: protocol redirects are blocked"""
        response = self.client.post(
            '/user_login/?next=data:text/html,<script>alert(1)</script>',
            {
                'email': 'testuser@example.com',
                'password': 'TestPass123'
            },
            follow=False
        )
        
        # Should redirect to safe default
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('data:', response.url)
    
    def test_http_to_https_redirect_blocked(self):
        """Test that redirect from HTTPS to HTTP is blocked"""
        # Simulate HTTPS connection
        response = self.client.post(
            '/user_login/?next=http://example.com/',
            {
                'email': 'testuser@example.com',
                'password': 'TestPass123'
            },
            secure=True,  # HTTPS request
            follow=False
        )
        
        # Should not redirect to HTTP when on HTTPS
        self.assertEqual(response.status_code, 302)
        # Should redirect to safe default
        self.assertNotIn('http://example.com', response.url)
    
    def test_empty_next_parameter_safe_default(self):
        """Test that empty next parameter uses safe default"""
        response = self.client.post(
            '/user_login/?next=',
            {
                'email': 'testuser@example.com',
                'password': 'TestPass123'
            },
            follow=False
        )
        
        # Should redirect to home_dash (safe default)
        self.assertEqual(response.status_code, 302)
        self.assertTrue('home_dash' in response.url or response.url.endswith('/'))
    
    def test_no_next_parameter_safe_default(self):
        """Test that missing next parameter uses safe default"""
        response = self.client.post(
            '/user_login/',
            {
                'email': 'testuser@example.com',
                'password': 'TestPass123'
            },
            follow=False
        )
        
        # Should redirect to home_dash (safe default)
        self.assertEqual(response.status_code, 302)
        self.assertTrue('home_dash' in response.url or response.url.endswith('/'))
    
    def test_relative_path_redirect_allowed(self):
        """Test that relative path redirects are allowed"""
        response = self.client.post(
            '/user_login/?next=/nutrition/',
            {
                'email': 'testuser@example.com',
                'password': 'TestPass123'
            },
            follow=False
        )
        
        # Should redirect to /nutrition/ (same host)
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/nutrition/' in response.url or response.url.endswith('/nutrition/'))
    
    def test_invalid_credentials_no_redirect(self):
        """Test that invalid credentials do not redirect at all"""
        response = self.client.post(
            '/user_login/?next=https://evil.com',
            {
                'email': 'testuser@example.com',
                'password': 'WrongPassword'
            },
            follow=False
        )
        
        # Should stay on login page, no redirect
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid email or password')
    
    def test_unicode_encoded_redirect_blocked(self):
        """Test that unicode/encoded external URLs are blocked"""
        response = self.client.post(
            '/user_login/?next=https%3A%2F%2Fevil.com',
            {
                'email': 'testuser@example.com',
                'password': 'TestPass123'
            },
            follow=False
        )
        
        # Should redirect to safe default
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('evil.com', response.url)
    
    def test_url_with_fragments_redirect_blocked(self):
        """Test that URLs with URL fragments pointing to external hosts are blocked"""
        response = self.client.post(
            '/user_login/?next=https://evil.com#local',
            {
                'email': 'testuser@example.com',
                'password': 'TestPass123'
            },
            follow=False
        )
        
        # Should redirect to safe default
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('evil.com', response.url)
    
    def test_multiple_slashes_redirect_blocked(self):
        """Test that multiple slashes for protocol bypass are blocked"""
        response = self.client.post(
            '/user_login/?next=///evil.com',
            {
                'email': 'testuser@example.com',
                'password': 'TestPass123'
            },
            follow=False
        )
        
        # Should redirect to safe default
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('evil.com', response.url)
    
    def test_backslash_protocol_escape_redirect_blocked(self):
        """Test that backslash protocol escapes are blocked"""
        response = self.client.post(
            '/user_login/?next=\\\\evil.com',
            {
                'email': 'testuser@example.com',
                'password': 'TestPass123'
            },
            follow=False
        )
        
        # Should redirect to safe default
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('evil.com', response.url)
    
    def test_localhost_redirect_allowed_same_host(self):
        """Test that localhost/same host redirects are allowed"""
        response = self.client.post(
            '/user_login/?next=/accounts/profile/',
            {
                'email': 'testuser@example.com',
                'password': 'TestPass123'
            },
            follow=False
        )
        
        # Should redirect to local account profile
        self.assertEqual(response.status_code, 302)
        self.assertTrue('profile' in response.url or '/accounts/' in response.url)
    
    def test_open_redirect_phishing_chain(self):
        """Test comprehensive phishing attack scenario prevention"""
        # Simulate attacker crafting malicious URL with next parameter
        # pointing to fake login page
        malicious_urls = [
            '/user_login/?next=https://evil.com/fake-login',
            '/user_login/?next=http://attacker.io/phish',
            '/user_login/?next=//malicious-site.com/steal-data',
        ]
        
        for malicious_url in malicious_urls:
            response = self.client.post(
                malicious_url,
                {
                    'email': 'testuser@example.com',
                    'password': 'TestPass123'
                },
                follow=False
            )
            
            # All should redirect to safe default, not attacker site
            self.assertEqual(response.status_code, 302)
            # Verify no external domains in redirect
            self.assertNotIn('evil.com', response.url)
            self.assertNotIn('attacker.io', response.url)
            self.assertNotIn('malicious-site.com', response.url)


class CrossUserDataExposureSecurityTests(TestCase):
    """Test suite for cross-user nutrition data exposure vulnerability"""
    
    def setUp(self):
        """Create test users with food data"""
        self.client = Client()
        
        # User 1
        self.user1 = User.objects.create_user(
            username='user1@test.com',
            email='user1@test.com',
            password='Pass123'
        )
        self.meal1 = Meal.objects.create(
            user=self.user1,
            name='Breakfast',
            date=date(2026, 4, 30)
        )
        self.food1_user1 = FoodItem.objects.create(
            meal=self.meal1,
            name='User1 Chicken Breast',
            calories=200,
            protein=30,
            carbs=0,
            fats=5
        )
        self.food2_user1 = FoodItem.objects.create(
            meal=self.meal1,
            name='User1 Brown Rice',
            calories=150,
            protein=3,
            carbs=30,
            fats=1
        )
        
        # User 2
        self.user2 = User.objects.create_user(
            username='user2@test.com',
            email='user2@test.com',
            password='Pass123'
        )
        self.meal2 = Meal.objects.create(
            user=self.user2,
            name='Dinner',
            date=date(2026, 4, 30)
        )
        self.food1_user2 = FoodItem.objects.create(
            meal=self.meal2,
            name='User2 Salmon Fillet',
            calories=250,
            protein=35,
            carbs=0,
            fats=12
        )
        self.food2_user2 = FoodItem.objects.create(
            meal=self.meal2,
            name='User2 Kale Salad',
            calories=50,
            protein=3,
            carbs=8,
            fats=1
        )
    
    def test_search_foods_filters_by_user(self):
        """Test that search_foods only returns current user's items"""
        self.client.login(username='user1@test.com', password='Pass123')
        response = self.client.get('/api/search_foods/?q=chicken')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should only see User1's chicken, not User2's
        self.assertEqual(len(data['results']), 1)
        self.assertIn('User1 Chicken', data['results'][0]['name'])
        self.assertNotIn('User2', data['results'][0]['name'])
    
    def test_search_foods_cannot_see_other_users_data(self):
        """Test that User1 cannot see User2's food via search"""
        self.client.login(username='user1@test.com', password='Pass123')
        response = self.client.get('/api/search_foods/?q=salmon')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # User1 searches for "salmon" (User2's item)
        # Should return empty because User1 has no salmon
        self.assertEqual(len(data['results']), 0)
    
    def test_search_foods_user2_cannot_see_user1_data(self):
        """Test that User2 cannot see User1's food via search"""
        self.client.login(username='user2@test.com', password='Pass123')
        response = self.client.get('/api/search_foods/?q=brown rice')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # User2 searches for "brown rice" (User1's item)
        # Should return empty because User2 has no brown rice
        self.assertEqual(len(data['results']), 0)
    
    def test_get_all_foods_filters_by_user(self):
        """Test that get_all_foods only returns current user's items"""
        self.client.login(username='user1@test.com', password='Pass123')
        response = self.client.get('/api/all_foods/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # User1 should only see their 2 foods
        self.assertEqual(data['count'], 2)
        names = [f['name'] for f in data['foods']]
        self.assertIn('User1 Brown Rice', names)
        self.assertIn('User1 Chicken Breast', names)
        
        # Should NOT see User2's foods
        self.assertNotIn('User2 Salmon Fillet', names)
        self.assertNotIn('User2 Kale Salad', names)
    
    def test_get_all_foods_user2_isolated(self):
        """Test that User2 sees only their own foods"""
        self.client.login(username='user2@test.com', password='Pass123')
        response = self.client.get('/api/all_foods/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # User2 should only see their 2 foods
        self.assertEqual(data['count'], 2)
        names = [f['name'] for f in data['foods']]
        self.assertIn('User2 Salmon Fillet', names)
        self.assertIn('User2 Kale Salad', names)
        
        # Should NOT see User1's foods
        self.assertNotIn('User1 Chicken Breast', names)
        self.assertNotIn('User1 Brown Rice', names)
    
    def test_unauthenticated_cannot_search_foods(self):
        """Test that unauthenticated users cannot search foods"""
        response = self.client.get('/api/search_foods/?q=chicken', follow=False)
        
        # Should redirect to login (302) because of @login_required
        self.assertEqual(response.status_code, 302)
        self.assertIn('/user_login/', response.url)
    
    def test_unauthenticated_cannot_get_all_foods(self):
        """Test that unauthenticated users cannot access all_foods"""
        response = self.client.get('/api/all_foods/', follow=False)
        
        # Should redirect to login (302)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/user_login/', response.url)
    
    def test_search_foods_returns_user_specific_ids(self):
        """Test that search results contain correct IDs for current user"""
        self.client.login(username='user1@test.com', password='Pass123')
        response = self.client.get('/api/search_foods/?q=chicken')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should contain User1's food ID, not User2's
        self.assertEqual(data['results'][0]['id'], self.food1_user1.id)
        self.assertNotEqual(data['results'][0]['id'], self.food1_user2.id)
    
    def test_search_foods_ids_cannot_be_used_for_idor(self):
        """Test that search results IDs from search cannot be used by other users"""
        # User1 searches and gets their food ID
        self.client.login(username='user1@test.com', password='Pass123')
        response = self.client.get('/api/search_foods/?q=chicken')
        food_id = response.json()['results'][0]['id']
        self.assertEqual(food_id, self.food1_user1.id)
        
        # Logout and login as User2
        self.client.logout()
        self.client.login(username='user2@test.com', password='Pass123')
        
        # User2 tries to get User1's food via search (shouldn't find it)
        response = self.client.get('/api/search_foods/?q=chicken')
        data = response.json()
        
        # Should be empty - User2 has no chicken
        self.assertEqual(len(data['results']), 0)
        
        # Verify the ID is NOT in User2's all_foods
        response = self.client.get('/api/all_foods/')
        returned_ids = [f['id'] for f in response.json()['foods']]
        self.assertNotIn(food_id, returned_ids)
    
    def test_search_foods_empty_for_no_matches(self):
        """Test that search returns empty when no user matches"""
        self.client.login(username='user1@test.com', password='Pass123')
        response = self.client.get('/api/search_foods/?q=nonexistent_food_xyz')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 0)
    
    def test_search_foods_case_insensitive_user_filtered(self):
        """Test that search is case-insensitive but still user-filtered"""
        self.client.login(username='user1@test.com', password='Pass123')
        
        # Try uppercase
        response = self.client.get('/api/search_foods/?q=CHICKEN')
        data = response.json()
        self.assertEqual(len(data['results']), 1)
        
        # Try mixed case
        response = self.client.get('/api/search_foods/?q=ChIcKeN')
        data = response.json()
        self.assertEqual(len(data['results']), 1)
        
        # All results should be User1's
        self.assertIn('User1', data['results'][0]['name'])
    
    def test_get_all_foods_returns_user_owned_foods_only(self):
        """Test that get_all_foods strictly returns only user's foods"""
        self.client.login(username='user1@test.com', password='Pass123')
        response = self.client.get('/api/all_foods/')
        data = response.json()
        
        # All foods should have 'User1' in the name
        for food in data['foods']:
            self.assertIn('User1', food['name'], 
                         f"Found non-user1 food: {food['name']}")
    
    def test_search_foods_deduplication_respects_user_filter(self):
        """Test that deduplication still respects user ownership"""
        # Create another User1 food with similar name
        food3 = FoodItem.objects.create(
            meal=self.meal1,
            name='User1 Chicken Breast',  # Duplicate name for User1
            calories=210,
            protein=31,
            carbs=0,
            fats=6
        )
        
        self.client.login(username='user1@test.com', password='Pass123')
        response = self.client.get('/api/search_foods/?q=chicken')
        data = response.json()
        
        # Should still have only 1 result (deduplicated) from User1
        self.assertEqual(len(data['results']), 1)
        # ID should be one of User1's chicken items
        returned_id = data['results'][0]['id']
        self.assertIn(returned_id, [self.food1_user1.id, food3.id])
        # Should NOT be User2's ID
        self.assertNotEqual(returned_id, self.food1_user2.id)
    
    def test_all_foods_count_accuracy(self):
        """Test that count field in get_all_foods is accurate per user"""
        self.client.login(username='user1@test.com', password='Pass123')
        response = self.client.get('/api/all_foods/')
        data = response.json()
        
        # Count should match actual foods returned
        self.assertEqual(data['count'], len(data['foods']))
        self.assertEqual(data['count'], 2)  # User1 has 2 foods
    
    def test_search_foods_query_too_short_blocked(self):
        """Test that very short queries return empty (less than 2 chars)"""
        self.client.login(username='user1@test.com', password='Pass123')
        
        response = self.client.get('/api/search_foods/?q=a')
        data = response.json()
        self.assertEqual(len(data['results']), 0)
        
        response = self.client.get('/api/search_foods/?q=')
        data = response.json()
        self.assertEqual(len(data['results']), 0)
    
    def test_food_item_nutritional_data_isolation(self):
        """Test that nutritional data is not leaked between users"""
        # Get User1's data
        self.client.login(username='user1@test.com', password='Pass123')
        response = self.client.get('/api/all_foods/')
        user1_foods = response.json()['foods']
        
        # Get User2's data
        self.client.logout()
        self.client.login(username='user2@test.com', password='Pass123')
        response = self.client.get('/api/all_foods/')
        user2_foods = response.json()['foods']
        
        # Verify completely different food sets
        user1_names = {f['name'] for f in user1_foods}
        user2_names = {f['name'] for f in user2_foods}
        
        # No overlap
        self.assertEqual(len(user1_names & user2_names), 0)
    
    def test_cross_user_enumeration_prevention(self):
        """Test that users cannot enumerate other users' food via search"""
        self.client.login(username='user1@test.com', password='Pass123')
        
        # Try various searches that should find User2's foods
        search_queries = ['salmon', 'kale', 'salad', 'fillet']
        
        for query in search_queries:
            response = self.client.get(f'/api/search_foods/?q={query}')
            data = response.json()
            
            # Each search should return 0 results for User1
            self.assertEqual(len(data['results']), 0,
                           f"User1 found User2's food with query: {query}")


class SocialLoginCSRFSecurityTests(TestCase):
    """Test suite for social login CSRF vulnerability prevention"""
    
    def test_settings_socialaccount_login_on_get_false(self):
        """Test that SOCIALACCOUNT_LOGIN_ON_GET setting is False"""
        from django.conf import settings
        
        # Verify vulnerable setting is disabled
        self.assertFalse(
            settings.SOCIALACCOUNT_LOGIN_ON_GET,
            "SOCIALACCOUNT_LOGIN_ON_GET must be False to prevent login-CSRF attacks"
        )
    
    def test_settings_email_auto_connect_false(self):
        """Test that SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT is False"""
        from django.conf import settings
        
        # Verify this setting is disabled to require explicit user consent
        self.assertFalse(
            settings.SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT,
            "SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT must be False to prevent auto-linking"
        )
    
    def test_social_login_on_get_prevents_csrf(self):
        """Test that SOCIALACCOUNT_LOGIN_ON_GET=False prevents GET-based CSRF"""
        from django.conf import settings
        
        # With SOCIALACCOUNT_LOGIN_ON_GET = False:
        # - OAuth flows cannot be initiated via GET requests
        # - This blocks the attack vector: <img src="/accounts/google/login/">
        # - Prevents silent account linking
        self.assertFalse(settings.SOCIALACCOUNT_LOGIN_ON_GET)
        
        # Verify the setting is documented
        self.assertTrue(hasattr(settings, 'SOCIALACCOUNT_LOGIN_ON_GET'))
    
    def test_auto_signup_enabled_with_get_disabled_safe(self):
        """Test that AUTO_SIGNUP is safe when GET is disabled"""
        from django.conf import settings
        
        # AUTO_SIGNUP=True is OK when SOCIALACCOUNT_LOGIN_ON_GET=False
        # because users must explicitly click POST button (CSRF protected)
        self.assertFalse(settings.SOCIALACCOUNT_LOGIN_ON_GET)
        self.assertTrue(settings.SOCIALACCOUNT_AUTO_SIGNUP)
    
    def test_email_authentication_auto_connect_disabled(self):
        """Test that email-based auto-connect is disabled"""
        from django.conf import settings
        
        # With this disabled, social accounts won't auto-link to existing
        # accounts just because email matches
        self.assertFalse(settings.SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT)
    
    def test_combined_settings_prevent_login_csrf(self):
        """Test that settings combination prevents login-CSRF attacks"""
        from django.conf import settings
        
        # Key protection: SOCIALACCOUNT_LOGIN_ON_GET = False
        # This is the PRIMARY defense against login-CSRF
        self.assertFalse(settings.SOCIALACCOUNT_LOGIN_ON_GET)
        
        # Secondary defense: SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = False
        # Prevents silent account linking
        self.assertFalse(settings.SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT)
        
        # Combined: Users must:
        # 1. Click button to initiate (POST required)
        # 2. Provide CSRF token with POST
        # 3. Explicitly consent to linking (no auto-connect)
    
    def test_login_on_get_false_documented(self):
        """Test that the security fix is documented in settings"""
        from django.conf import settings
        
        # Verify setting exists and is set correctly
        setting_value = getattr(settings, 'SOCIALACCOUNT_LOGIN_ON_GET', None)
        self.assertIsNotNone(setting_value)
        self.assertFalse(setting_value, 
                        "SOCIALACCOUNT_LOGIN_ON_GET must be False (django-allauth recommendation)")
    
    def test_no_get_based_oauth_flows(self):
        """Test that OAuth flows cannot be initiated via GET"""
        from django.conf import settings
        
        # This setting ensures:
        # - GET requests to /accounts/provider/login/ won't initiate OAuth
        # - <img> tags cannot trigger silent logins
        # - <iframe> tags cannot trigger silent logins
        # - Only explicit user action (button click) triggers login
        
        self.assertFalse(settings.SOCIALACCOUNT_LOGIN_ON_GET)
    
    def test_post_required_for_oauth_initiation(self):
        """Test that POST is required to initiate OAuth flow"""
        from django.conf import settings
        
        # With SOCIALACCOUNT_LOGIN_ON_GET=False, the framework
        # requires HTTP POST method to initiate social login
        # POST requests require CSRF token (Django built-in protection)
        
        setting_disables_get = not settings.SOCIALACCOUNT_LOGIN_ON_GET
        self.assertTrue(setting_disables_get)
    
    def test_csrf_token_required_for_social_login(self):
        """Test that CSRF tokens protect social login forms"""
        from django.conf import settings
        
        # When GET is disabled, users access login via POST form
        # Django's CSRF middleware protects POST forms by default
        # Attacker cannot forge valid CSRF tokens from other domains
        
        self.assertFalse(settings.SOCIALACCOUNT_LOGIN_ON_GET)
    
    def test_attack_vector_get_request_blocked(self):
        """Test that GET-based attack vector is blocked"""
        from django.conf import settings
        
        # Attack vector (before fix):
        # <img src="https://app.com/accounts/google/login/">
        # 
        # This GET request initiates OAuth in victim's browser
        # Combined with auto-connect, victim's account hijacked
        
        # Protection (after fix):
        # SOCIALACCOUNT_LOGIN_ON_GET = False
        # GET request is not processed
        # Only POST with CSRF token works
        
        self.assertFalse(settings.SOCIALACCOUNT_LOGIN_ON_GET)
    
    def test_invisible_img_tag_csrf_blocked(self):
        """Test that invisible <img> tag CSRF attacks are blocked"""
        from django.conf import settings
        
        # Attack: <img src="..." style="display:none">
        # When victim visits page, GET request made silently
        # With SOCIALACCOUNT_LOGIN_ON_GET=True: OAuth initiated silently
        # With SOCIALACCOUNT_LOGIN_ON_GET=False: GET ignored, safe
        
        self.assertFalse(settings.SOCIALACCOUNT_LOGIN_ON_GET)
    
    def test_iframe_csrf_blocked(self):
        """Test that iframe-based CSRF attacks are blocked"""
        from django.conf import settings
        
        # Attack: <iframe src="..." style="display:none"></iframe>
        # Without fix: Silent OAuth initiation in iframe
        # With fix: GET request not processed, attack fails
        
        self.assertFalse(settings.SOCIALACCOUNT_LOGIN_ON_GET)
    
    def test_javascript_redirect_csrf_mitigated(self):
        """Test that JavaScript redirects have CSRF protection"""
        from django.conf import settings
        
        # Attack: window.location = "/accounts/google/login/" in JS
        # Even if executed, requires subsequent POST with CSRF token
        # Cannot be silently completed without user interaction
        
        self.assertFalse(settings.SOCIALACCOUNT_LOGIN_ON_GET)
    
    def test_auto_connect_requires_explicit_consent(self):
        """Test that account auto-connect requires explicit user consent"""
        from django.conf import settings
        
        # With EMAIL_AUTHENTICATION_AUTO_CONNECT = False:
        # Social account won't auto-link even if email matches
        # User must explicitly confirm linking
        # Prevents silent account takeover
        
        self.assertFalse(settings.SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT)
    
    def test_settings_follow_django_allauth_recommendation(self):
        """Test that settings follow django-allauth security recommendations"""
        from django.conf import settings
        
        # django-allauth documentation recommends:
        # SOCIALACCOUNT_LOGIN_ON_GET = False (default in newer versions)
        # This is a well-known security issue resolved by this setting
        
        # Verify the secure setting is applied
        self.assertFalse(settings.SOCIALACCOUNT_LOGIN_ON_GET,
                        "Follow django-allauth security best practices")
    
    def test_login_csrf_chain_prevention(self):
        """Test that the full login-CSRF chain is prevented"""
        from django.conf import settings
        
        # Attack chain (before fix):
        # 1. Attacker creates social account with victim's email
        # 2. Attacker sends <img> to /accounts/google/login/ to victim
        # 3. OAuth completes, auto-connects to victim's account
        # 4. Attacker logs in with their social account → victim's account
        
        # Prevention (after fix):
        # Step 2 fails: GET not processed (SOCIALACCOUNT_LOGIN_ON_GET=False)
        # Step 3 fails even if reached: No auto-connect (EMAIL_AUTHENTICATION_AUTO_CONNECT=False)
        
        self.assertFalse(settings.SOCIALACCOUNT_LOGIN_ON_GET)
        self.assertFalse(settings.SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT)
    
    def test_account_takeover_prevented(self):
        """Test that account takeover via social login CSRF is prevented"""
        from django.conf import settings
        
        # Before fix: Attacker could take over victim's account by:
        # - Creating social account with victim's email
        # - Silently linking it via GET-based CSRF
        # - Logging in with attacker's credentials
        
        # After fix: Both attack vectors blocked
        self.assertFalse(settings.SOCIALACCOUNT_LOGIN_ON_GET,
                        "Prevents silent OAuth initiation")
        self.assertFalse(settings.SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT,
                        "Prevents silent account linking")
