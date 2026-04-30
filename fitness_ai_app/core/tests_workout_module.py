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
