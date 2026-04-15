# Exercise Database Documentation

## Overview

The Exercise Database is a comprehensive system for storing, organizing, and filtering exercises based on multiple criteria including type, muscle groups, equipment, location, difficulty, and user injuries.

## Database Structure

### Models

#### 1. **ExerciseType**
Classification of exercises by training focus.
- Strength
- Toning/Endurance
- Cardio
- Flexibility
- Rehab

```python
ExerciseType.objects.all()  # Get all exercise types
```

#### 2. **MuscleGroup**
Primary muscle groupings for broader categorization.
- Upper Body
- Lower Body
- Core
- Full Body

#### 3. **Muscle**
Specific individual muscles for detailed tracking (used for injury exclusion and visualization).
- Triceps, Biceps, Forearms, Shoulders, Chest, Back, Lats
- Quadriceps, Hamstrings, Glutes, Calves, Hip Flexors, Adductors
- Abs, Obliques, Lower Back, Transverse Abdominis

#### 4. **Equipment**
Available equipment types for home or gym use.
- Body Weight
- Dumbbells
- Barbell
- Kettlebell
- Pull-up Bar
- Bench
- Resistance Band
- Treadmill
- Exercise Bike
- Rowing Machine
- Yoga Mat

#### 5. **TrainingExercise**
Main exercise database with comprehensive details.

Key Fields:
- `name` - Exercise name
- `description` - What the exercise does
- `instructions` - Step-by-step guide
- `difficulty` - Beginner, Intermediate, Advanced
- `exercise_type` - Link to ExerciseType
- `muscle_groups` - Related muscle groups
- `primary_muscles` - Muscles primarily targeted
- `secondary_muscles` - Muscles secondarily involved
- `location` - At Home, At Gym, or Both
- `equipment` - Required equipment
- `default_sets` - Recommended sets
- `default_reps` - Recommended reps
- `default_duration_seconds` - For timed exercises
- `high_impact` - Boolean for impact level
- `joint_stress` - Text description of stress
- `is_active` - Active/inactive flag

#### 6. **UserInjury**
Track user injuries to exclude exercises affecting injured areas.

Fields:
- `user` - User with injury
- `muscle` - Injured muscle
- `severity` - Mild, Moderate, Severe
- `notes` - Additional information
- `start_date` - Injury start date
- `end_date` - Recovery date (null if ongoing)
- `is_active` - Currently active injury

#### 7. **UserEquipmentProfile**
Track equipment available to each user.

Fields:
- `user` - Associated user
- `location` - At Home or At Gym
- `equipment` - Available equipment (M2M)

## API Endpoints

All endpoints require authentication except those noted otherwise.

### 1. Get Exercise Types
**GET** `/api/exercises/types/`

Response:
```json
{
  "exercise_types": [
    {
      "id": 1,
      "name": "Strength",
      "description": "Build muscle and increase maximum strength"
    }
  ]
}
```

### 2. Get Muscle Groups
**GET** `/api/exercises/muscle-groups/`

Response:
```json
{
  "muscle_groups": [
    {
      "id": 1,
      "name": "Upper Body",
      "description": "Arms, shoulders, chest, and back"
    }
  ]
}
```

### 3. Get Muscles
**GET** `/api/exercises/muscles/`

Query Parameters:
- `group_id` (optional) - Filter by muscle group ID

Response:
```json
{
  "muscles": [
    {
      "id": 1,
      "name": "Biceps",
      "muscle_group__name": "Upper Body",
      "description": "Biceps muscle"
    }
  ]
}
```

### 4. Get Equipment
**GET** `/api/exercises/equipment/`

Response:
```json
{
  "equipment": [
    {
      "id": 1,
      "name": "Dumbbells",
      "description": "Free weights for individual hands"
    }
  ]
}
```

### 5. Filter Exercises
**GET** `/api/exercises/filter/` (Requires login)

Query Parameters:
- `exercise_type` - Exercise type ID
- `muscle_group` - Muscle group ID
- `muscle` - Specific muscle ID
- `equipment` - Comma-separated equipment IDs
- `location` - 'home', 'gym', or 'both'
- `difficulty` - 'beginner', 'intermediate', 'advanced'
- `exclude_injured` - 'true' to exclude exercises affecting injured muscles

Example:
```
GET /api/exercises/filter/?exercise_type=1&location=gym&difficulty=intermediate
```

Response:
```json
{
  "count": 5,
  "exercises": [
    {
      "id": 1,
      "name": "Barbell Bench Press",
      "description": "Compound pressing movement targeting chest, shoulders, and triceps",
      "instructions": "1. Lie on bench...",
      "difficulty": "Intermediate",
      "exercise_type": {
        "id": 1,
        "name": "Strength"
      },
      "muscle_groups": [
        {
          "id": 1,
          "name": "Upper Body"
        }
      ],
      "primary_muscles": [
        {"id": 13, "name": "Chest"},
        {"id": 1, "name": "Triceps"}
      ],
      "secondary_muscles": [
        {"id": 15, "name": "Forearms"}
      ],
      "location": "At Gym",
      "equipment": [
        {"id": 3, "name": "Barbell"},
        {"id": 6, "name": "Bench"}
      ],
      "default_sets": 4,
      "default_reps": 6,
      "default_duration_seconds": null,
      "high_impact": false,
      "joint_stress": "shoulders, elbows, wrists"
    }
  ]
}
```

### 6. Get User-Safe Exercises
**GET** `/api/exercises/safe/` (Requires login)

Gets exercises safe for the user based on injuries and equipment.

Query Parameters:
- `location` - 'home' or 'gym' (default: 'gym')
- `exercise_type` - Exercise type ID (optional)
- `muscle_group` - Muscle group ID (optional)

Response: Same as filter endpoint

### 7. Get Exercise Detail
**GET** `/api/exercises/<exercise_id>/`

Response: Detailed exercise object (same format as filter results)

### 8. Add User Injury
**POST** `/api/user/injury/add/` (Requires login)

Request Body:
```json
{
  "muscle_id": 1,
  "severity": "moderate",
  "notes": "Sports injury while playing basketball"
}
```

Response:
```json
{
  "success": true,
  "injury_id": 5,
  "message": "Injury recorded successfully"
}
```

### 9. Update User Equipment
**POST** `/api/user/equipment/` (Requires login)

Request Body:
```json
{
  "location": "home",
  "equipment": [1, 2, 5, 11]
}
```

Response:
```json
{
  "success": true,
  "message": "Equipment profile updated"
}
```

## Admin Interface

All models are registered in Django admin for easy management:

```
/admin/core/exercisetype/
/admin/core/musclegroup/
/admin/core/muscle/
/admin/core/equipment/
/admin/core/trainingexercise/
/admin/core/userinjury/
/admin/core/userequipmentprofile/
```

### Adding New Exercises

1. Go to `/admin/core/trainingexercise/`
2. Click "Add Training Exercise"
3. Fill in all fields:
   - Basic info (name, description, instructions)
   - Classification (type, muscle groups, specific muscles)
   - Location & Equipment
   - Default settings (sets, reps, duration)
   - Injury considerations (high impact, joint stress)
4. Save

### Managing User Injuries

1. Go to `/admin/core/userinjury/`
2. Create new injury entry
3. Select user, muscle, severity
4. Set start_date and optional end_date
5. Mark as active/inactive

## Usage Examples

### JavaScript Frontend Example

```javascript
// Get all exercises for strength training at home
fetch('/api/exercises/filter/?exercise_type=1&location=home')
  .then(res => res.json())
  .then(data => console.log(data.exercises));

// Get safe exercises excluding injured areas
fetch('/api/exercises/safe/?location=gym&exclude_injured=true')
  .then(res => res.json())
  .then(data => console.log(data.exercises));

// Get exercises for specific muscle group
fetch('/api/exercises/filter/?muscle_group=1&difficulty=beginner')
  .then(res => res.json())
  .then(data => console.log(data.exercises));

// Record a user injury
fetch('/api/user/injury/add/', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    muscle_id: 5,
    severity: 'moderate',
    notes: 'Shoulder strain from overhead press'
  })
});

// Update user equipment
fetch('/api/user/equipment/', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    location: 'home',
    equipment: [1, 2, 11]  // Body Weight, Dumbbells, Yoga Mat
  })
});
```

### Python Usage

```python
from core.models import TrainingExercise, UserInjury, UserEquipmentProfile

# Filter exercises
strength_exercises = TrainingExercise.objects.filter(
    exercise_type__name='Strength',
    difficulty='intermediate'
)

# Get exercises affecting specific muscle
bicep_exercises = TrainingExercise.objects.filter(
    primary_muscles__name='Biceps'
)

# Get user's active injuries
user_injuries = UserInjury.objects.filter(
    user=request.user,
    is_active=True
)

# Exclude exercises affecting injured muscles
safe_exercises = TrainingExercise.objects.exclude(
    primary_muscles__in=[inj.muscle for inj in user_injuries]
)
```

## Database Statistics

- **Exercise Types**: 5
- **Muscle Groups**: 4
- **Specific Muscles**: 17
- **Equipment Options**: 11
- **Pre-loaded Exercises**: 18

### Pre-loaded Exercise Breakdown:

**Strength (5):**
- Barbell Bench Press
- Dumbbell Curl
- Pull-ups
- Tricep Dips
- Barbell Back Squat
- Dumbbell Lunges
- Romanian Deadlift
- Barbell Deadlift
- Plank

**Cardio (3):**
- Running
- Cycling
- Rowing

**Toning/Endurance (2):**
- High-Intensity Interval Training (HIIT)
- Push-ups

**Flexibility (2):**
- Yoga
- Foam Rolling

**Rehab (2):**
- Shoulder Rehabilitation
- Knee Strengthening

## Management Command

Populate the database with sample data:

```bash
python manage.py populate_exercise_db
```

This creates all exercise types, muscle groups, equipment, and 18 sample exercises.

## Key Features

✅ **Comprehensive Filtering** - Filter by type, muscle, equipment, location, difficulty
✅ **Injury Tracking** - Automatically exclude exercises affecting injured areas
✅ **Equipment Profiles** - Store available equipment per user
✅ **Admin Interface** - Easy management and data entry
✅ **API Endpoints** - RESTful access to all data
✅ **Detailed Instructions** - Step-by-step guides for each exercise
✅ **Impact Classification** - Mark high-impact exercises
✅ **Muscle Targeting** - Track primary and secondary muscles
✅ **Location-based** - Filter for home or gym exercises
✅ **Difficulty Levels** - Beginner to Advanced exercises

## Future Enhancements

- Video/GIF demonstrations for each exercise
- User ratings and reviews
- Workout plan templates
- Exercise progression tracking
- Social features (share workouts)
- Machine learning recommendations
- Integration with fitness trackers
