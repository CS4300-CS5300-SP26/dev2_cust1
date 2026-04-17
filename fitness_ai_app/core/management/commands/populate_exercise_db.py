"""
Management command to populate the exercise database with comprehensive exercise data
Usage: python manage.py populate_exercise_db
"""

from django.core.management.base import BaseCommand
from core.models import (
    ExerciseType, MuscleGroup, Muscle, Equipment, TrainingExercise
)


class Command(BaseCommand):
    help = 'Populate the exercise database with exercises and metadata'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting exercise database population...'))

        # Create Exercise Types
        self.stdout.write('Creating exercise types...')
        exercise_types = {
            'strength': ExerciseType.objects.get_or_create(
                name='Strength',
                defaults={'description': 'Build muscle and increase maximum strength'}
            )[0],
            'endurance': ExerciseType.objects.get_or_create(
                name='Toning/Endurance',
                defaults={'description': 'Tone muscles and build muscular endurance'}
            )[0],
            'cardio': ExerciseType.objects.get_or_create(
                name='Cardio',
                defaults={'description': 'Cardiovascular exercise for heart and lung health'}
            )[0],
            'flexibility': ExerciseType.objects.get_or_create(
                name='Flexibility',
                defaults={'description': 'Improve range of motion and flexibility'}
            )[0],
            'rehab': ExerciseType.objects.get_or_create(
                name='Rehab',
                defaults={'description': 'Rehabilitation exercises for recovery'}
            )[0],
        }

        # Create Muscle Groups
        self.stdout.write('Creating muscle groups...')
        muscle_groups = {
            'upper_body': MuscleGroup.objects.get_or_create(
                name='Upper Body',
                defaults={'description': 'Arms, shoulders, chest, and back'}
            )[0],
            'lower_body': MuscleGroup.objects.get_or_create(
                name='Lower Body',
                defaults={'description': 'Legs, glutes, and hips'}
            )[0],
            'core': MuscleGroup.objects.get_or_create(
                name='Core',
                defaults={'description': 'Abdominals and back muscles'}
            )[0],
            'full_body': MuscleGroup.objects.get_or_create(
                name='Full Body',
                defaults={'description': 'Exercises engaging multiple muscle groups'}
            )[0],
        }

        # Create Specific Muscles
        self.stdout.write('Creating specific muscles...')
        muscles = {}

        # Upper body muscles
        for muscle_name in ['Triceps', 'Biceps', 'Forearms', 'Shoulders', 'Chest', 'Back', 'Lats']:
            muscle, _ = Muscle.objects.get_or_create(
                name=muscle_name,
                defaults={'muscle_group': muscle_groups['upper_body'], 'description': f'{muscle_name} muscle'}
            )
            muscles[muscle_name.lower()] = muscle

        # Lower body muscles
        for muscle_name in ['Quadriceps', 'Hamstrings', 'Glutes', 'Calves', 'Hip Flexors', 'Adductors']:
            muscle, _ = Muscle.objects.get_or_create(
                name=muscle_name,
                defaults={'muscle_group': muscle_groups['lower_body'], 'description': f'{muscle_name} muscle'}
            )
            muscles[muscle_name.lower()] = muscle

        # Core muscles
        for muscle_name in ['Abs', 'Obliques', 'Lower Back', 'Transverse Abdominis']:
            muscle, _ = Muscle.objects.get_or_create(
                name=muscle_name,
                defaults={'muscle_group': muscle_groups['core'], 'description': f'{muscle_name} muscle'}
            )
            muscles[muscle_name.lower()] = muscle

        # Create Equipment
        self.stdout.write('Creating equipment...')
        equipment_list = {
            'bodyweight': Equipment.objects.get_or_create(
                name='Body Weight',
                defaults={'description': 'No equipment needed'}
            )[0],
            'dumbbells': Equipment.objects.get_or_create(
                name='Dumbbells',
                defaults={'description': 'Free weights for individual hands'}
            )[0],
            'barbell': Equipment.objects.get_or_create(
                name='Barbell',
                defaults={'description': 'Long bar for heavy compound lifts'}
            )[0],
            'kettlebell': Equipment.objects.get_or_create(
                name='Kettlebell',
                defaults={'description': 'Ball-shaped weight with handle'}
            )[0],
            'pullup_bar': Equipment.objects.get_or_create(
                name='Pull-up Bar',
                defaults={'description': 'Bar for pull-ups and hanging exercises'}
            )[0],
            'bench': Equipment.objects.get_or_create(
                name='Bench',
                defaults={'description': 'Weight bench for pressing exercises'}
            )[0],
            'resistance_band': Equipment.objects.get_or_create(
                name='Resistance Band',
                defaults={'description': 'Elastic band for resistance training'}
            )[0],
            'treadmill': Equipment.objects.get_or_create(
                name='Treadmill',
                defaults={'description': 'Cardio equipment for running'}
            )[0],
            'exercise_bike': Equipment.objects.get_or_create(
                name='Exercise Bike',
                defaults={'description': 'Stationary bike for cardio'}
            )[0],
            'rowing_machine': Equipment.objects.get_or_create(
                name='Rowing Machine',
                defaults={'description': 'Equipment for rowing exercises'}
            )[0],
            'yoga_mat': Equipment.objects.get_or_create(
                name='Yoga Mat',
                defaults={'description': 'Mat for floor exercises'}
            )[0],
        }

        # Create Sample Exercises
        self.stdout.write('Creating exercises...')
        exercises_data = [
            # STRENGTH - Upper Body
            {
                'name': 'Barbell Bench Press',
                'exercise_type': exercise_types['strength'],
                'difficulty': 'intermediate',
                'description': 'Compound pressing movement targeting chest, shoulders, and triceps',
                'instructions': '1. Lie on bench with barbell at chest level\n2. Lower bar to chest\n3. Press bar up explosively\n4. Control descent and repeat',
                'location': 'gym',
                'muscle_groups': [muscle_groups['upper_body']],
                'primary_muscles': [muscles['chest'], muscles['triceps'], muscles['shoulders']],
                'secondary_muscles': [muscles['forearms']],
                'equipment': [equipment_list['barbell'], equipment_list['bench']],
                'default_sets': 4,
                'default_reps': 6,
                'joint_stress': 'shoulders, elbows, wrists',
            },
            {
                'name': 'Dumbbell Curl',
                'exercise_type': exercise_types['strength'],
                'difficulty': 'beginner',
                'description': 'Isolated biceps strengthening exercise',
                'instructions': '1. Stand with dumbbells at sides\n2. Curl weights up to shoulders\n3. Control descent\n4. Repeat',
                'location': 'both',
                'muscle_groups': [muscle_groups['upper_body']],
                'primary_muscles': [muscles['biceps']],
                'secondary_muscles': [muscles['forearms']],
                'equipment': [equipment_list['dumbbells']],
                'default_sets': 3,
                'default_reps': 10,
            },
            {
                'name': 'Pull-ups',
                'exercise_type': exercise_types['strength'],
                'difficulty': 'advanced',
                'description': 'Upper body pulling exercise for back and biceps',
                'instructions': '1. Grab bar with hands shoulder-width apart\n2. Pull body up until chin over bar\n3. Lower with control\n4. Repeat',
                'location': 'gym',
                'muscle_groups': [muscle_groups['upper_body']],
                'primary_muscles': [muscles['lats'], muscles['biceps']],
                'secondary_muscles': [muscles['back'], muscles['shoulders']],
                'equipment': [equipment_list['pullup_bar']],
                'default_sets': 3,
                'default_reps': 8,
            },
            {
                'name': 'Tricep Dips',
                'exercise_type': exercise_types['strength'],
                'difficulty': 'intermediate',
                'description': 'Upper body pressing exercise for triceps',
                'instructions': '1. Support yourself on parallel bars\n2. Lower body by bending elbows\n3. Push back up to start\n4. Repeat',
                'location': 'gym',
                'muscle_groups': [muscle_groups['upper_body']],
                'primary_muscles': [muscles['triceps']],
                'secondary_muscles': [muscles['chest'], muscles['shoulders']],
                'equipment': [equipment_list['bodyweight']],
                'default_sets': 3,
                'default_reps': 8,
            },
            
            # STRENGTH - Lower Body
            {
                'name': 'Barbell Back Squat',
                'exercise_type': exercise_types['strength'],
                'difficulty': 'advanced',
                'description': 'Compound leg exercise targeting quads, hamstrings, and glutes',
                'instructions': '1. Position barbell across shoulders\n2. Lower body by bending knees\n3. Keep chest up and weight in heels\n4. Return to standing position',
                'location': 'gym',
                'muscle_groups': [muscle_groups['lower_body']],
                'primary_muscles': [muscles['quadriceps'], muscles['glutes'], muscles['hamstrings']],
                'secondary_muscles': [muscles['lower back']],
                'equipment': [equipment_list['barbell'], equipment_list['bench']],
                'default_sets': 4,
                'default_reps': 6,
                'joint_stress': 'knees, ankles, lower back',
            },
            {
                'name': 'Dumbbell Lunges',
                'exercise_type': exercise_types['strength'],
                'difficulty': 'intermediate',
                'description': 'Single-leg exercise for quads and glutes',
                'instructions': '1. Hold dumbbells at sides\n2. Step forward and lower hips\n3. Front knee reaches 90 degrees\n4. Return and alternate legs',
                'location': 'both',
                'muscle_groups': [muscle_groups['lower_body']],
                'primary_muscles': [muscles['quadriceps'], muscles['glutes']],
                'secondary_muscles': [muscles['hamstrings']],
                'equipment': [equipment_list['dumbbells']],
                'default_sets': 3,
                'default_reps': 10,
            },
            {
                'name': 'Romanian Deadlift',
                'exercise_type': exercise_types['strength'],
                'difficulty': 'intermediate',
                'description': 'Hip hinge movement targeting hamstrings and glutes',
                'instructions': '1. Stand with feet hip-width apart holding barbell\n2. Push hips back while keeping legs straight\n3. Feel hamstring stretch\n4. Return to standing',
                'location': 'gym',
                'muscle_groups': [muscle_groups['lower_body']],
                'primary_muscles': [muscles['hamstrings'], muscles['glutes']],
                'secondary_muscles': [muscles['lower back']],
                'equipment': [equipment_list['barbell']],
                'default_sets': 3,
                'default_reps': 8,
            },

            # STRENGTH - Core
            {
                'name': 'Barbell Deadlift',
                'exercise_type': exercise_types['strength'],
                'difficulty': 'advanced',
                'description': 'Full-body compound movement with emphasis on posterior chain',
                'instructions': '1. Stand with feet under barbell\n2. Grip with hands just outside legs\n3. Pull bar from ground to hip height\n4. Lower with control',
                'location': 'gym',
                'muscle_groups': [muscle_groups['full_body']],
                'primary_muscles': [muscles['glutes'], muscles['hamstrings'], muscles['lower back']],
                'secondary_muscles': [muscles['biceps'], muscles['forearms']],
                'equipment': [equipment_list['barbell']],
                'default_sets': 3,
                'default_reps': 5,
                'joint_stress': 'lower back, knees, hips',
            },
            {
                'name': 'Plank',
                'exercise_type': exercise_types['strength'],
                'difficulty': 'beginner',
                'description': 'Isometric core exercise for abdominal strength',
                'instructions': '1. Support body on forearms and toes\n2. Keep body in straight line\n3. Engage core throughout\n4. Hold for time',
                'location': 'both',
                'muscle_groups': [muscle_groups['core']],
                'primary_muscles': [muscles['abs'], muscles['transverse abdominis']],
                'secondary_muscles': [muscles['obliques'], muscles['lower back']],
                'equipment': [equipment_list['yoga_mat']],
                'default_sets': 3,
                'default_duration_seconds': 60,
            },

            # CARDIO
            {
                'name': 'Running',
                'exercise_type': exercise_types['cardio'],
                'difficulty': 'intermediate',
                'description': 'Steady-state cardiovascular exercise',
                'instructions': '1. Warm up with light jogging\n2. Run at moderate pace for duration\n3. Cool down with walking\n4. Stretch afterwards',
                'location': 'both',
                'muscle_groups': [muscle_groups['full_body'], muscle_groups['lower_body']],
                'primary_muscles': [muscles['quadriceps'], muscles['hamstrings'], muscles['calves']],
                'secondary_muscles': [muscles['glutes']],
                'equipment': [equipment_list['treadmill']],
                'default_duration_seconds': 1200,
                'high_impact': True,
                'joint_stress': 'knees, ankles, hips',
            },
            {
                'name': 'Cycling',
                'exercise_type': exercise_types['cardio'],
                'difficulty': 'beginner',
                'description': 'Low-impact cardiovascular exercise',
                'instructions': '1. Set appropriate seat height\n2. Pedal at steady cadence\n3. Maintain moderate intensity\n4. Cool down after',
                'location': 'gym',
                'muscle_groups': [muscle_groups['lower_body'], muscle_groups['full_body']],
                'primary_muscles': [muscles['quadriceps'], muscles['calves'], muscles['glutes']],
                'secondary_muscles': [muscles['hamstrings']],
                'equipment': [equipment_list['exercise_bike']],
                'default_duration_seconds': 1200,
            },
            {
                'name': 'Rowing',
                'exercise_type': exercise_types['cardio'],
                'difficulty': 'intermediate',
                'description': 'Full-body cardio exercise with upper body emphasis',
                'instructions': '1. Sit with feet secured\n2. Drive with legs while pulling handle\n3. Extend arms at finish\n4. Reverse motion smoothly',
                'location': 'gym',
                'muscle_groups': [muscle_groups['full_body']],
                'primary_muscles': [muscles['lats'], muscles['hamstrings'], muscles['glutes']],
                'secondary_muscles': [muscles['back'], muscles['biceps']],
                'equipment': [equipment_list['rowing_machine']],
                'default_duration_seconds': 1200,
            },

            # ENDURANCE
            {
                'name': 'High-Intensity Interval Training (HIIT)',
                'exercise_type': exercise_types['endurance'],
                'difficulty': 'advanced',
                'description': 'Alternating high and low intensity intervals for endurance building',
                'instructions': '1. Warm up thoroughly\n2. Perform 30 sec high intensity\n3. Rest 30 sec low intensity\n4. Repeat 8-10 rounds',
                'location': 'both',
                'muscle_groups': [muscle_groups['full_body']],
                'primary_muscles': [muscles['quadriceps'], muscles['hamstrings'], muscles['glutes']],
                'secondary_muscles': [muscles['calves']],
                'equipment': [equipment_list['bodyweight']],
                'default_sets': 8,
                'default_duration_seconds': 60,
            },
            {
                'name': 'Push-ups',
                'exercise_type': exercise_types['endurance'],
                'difficulty': 'beginner',
                'description': 'Upper body endurance exercise using body weight',
                'instructions': '1. Position hands under shoulders\n2. Lower body until chest near floor\n3. Push back to start\n4. Repeat for reps/time',
                'location': 'both',
                'muscle_groups': [muscle_groups['upper_body']],
                'primary_muscles': [muscles['chest'], muscles['triceps'], muscles['shoulders']],
                'secondary_muscles': [muscles['forearms'], muscles['abs']],
                'equipment': [equipment_list['bodyweight']],
                'default_sets': 3,
                'default_reps': 15,
            },

            # FLEXIBILITY
            {
                'name': 'Yoga',
                'exercise_type': exercise_types['flexibility'],
                'difficulty': 'beginner',
                'description': 'Mind-body practice improving flexibility and balance',
                'instructions': '1. Follow instructor or video\n2. Hold poses with proper alignment\n3. Focus on breathing\n4. Cool down with savasana',
                'location': 'both',
                'muscle_groups': [muscle_groups['full_body']],
                'primary_muscles': [muscles['hamstrings'], muscles['hip flexors']],
                'secondary_muscles': [muscles['shoulders'], muscles['back']],
                'equipment': [equipment_list['yoga_mat']],
                'default_duration_seconds': 1800,
            },
            {
                'name': 'Foam Rolling',
                'exercise_type': exercise_types['flexibility'],
                'difficulty': 'beginner',
                'description': 'Self-myofascial release for muscle recovery and flexibility',
                'instructions': '1. Position foam roller under muscle\n2. Roll slowly over tender points\n3. Pause on tight spots for 30 sec\n4. Work entire muscle group',
                'location': 'both',
                'muscle_groups': [muscle_groups['full_body']],
                'primary_muscles': [muscles['hamstrings'], muscles['quadriceps'], muscles['lats']],
                'secondary_muscles': [muscles['calves'], muscles['forearms']],
                'equipment': [equipment_list['yoga_mat']],
                'default_duration_seconds': 900,
            },

            # REHAB
            {
                'name': 'Shoulder Rehabilitation',
                'exercise_type': exercise_types['rehab'],
                'difficulty': 'beginner',
                'description': 'Gentle shoulder exercises for injury recovery',
                'instructions': '1. Start with light resistance band\n2. Perform slow, controlled movements\n3. Focus on form over weight\n4. Avoid pain',
                'location': 'both',
                'muscle_groups': [muscle_groups['upper_body']],
                'primary_muscles': [muscles['shoulders']],
                'secondary_muscles': [muscles['back']],
                'equipment': [equipment_list['resistance_band']],
                'default_sets': 2,
                'default_reps': 15,
            },
            {
                'name': 'Knee Strengthening',
                'exercise_type': exercise_types['rehab'],
                'difficulty': 'beginner',
                'description': 'Controlled exercises for knee injury recovery',
                'instructions': '1. Perform isometric holds\n2. Slow range of motion\n3. Build strength gradually\n4. Follow PT protocol',
                'location': 'both',
                'muscle_groups': [muscle_groups['lower_body']],
                'primary_muscles': [muscles['quadriceps']],
                'secondary_muscles': [muscles['hamstrings'], muscles['glutes']],
                'equipment': [equipment_list['resistance_band']],
                'default_sets': 3,
                'default_reps': 12,
            },
        ]

        for exc_data in exercises_data:
            muscle_groups_list = exc_data.pop('muscle_groups')
            primary_muscles_list = exc_data.pop('primary_muscles')
            secondary_muscles_list = exc_data.pop('secondary_muscles')
            equipment_list_data = exc_data.pop('equipment')

            exercise, created = TrainingExercise.objects.get_or_create(
                name=exc_data['name'],
                defaults=exc_data
            )

            if created:
                exercise.muscle_groups.set(muscle_groups_list)
                exercise.primary_muscles.set(primary_muscles_list)
                exercise.secondary_muscles.set(secondary_muscles_list)
                exercise.equipment.set(equipment_list_data)
                self.stdout.write(f"✓ Created: {exercise.name}")
            else:
                self.stdout.write(f"→ Already exists: {exercise.name}")

        self.stdout.write(self.style.SUCCESS('✓ Exercise database population complete!'))
