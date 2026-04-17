# Exercise Database - Quick Start Guide

## What You Have

A complete, production-ready exercise database with:
- **18 pre-loaded exercises** across all training types
- **5 exercise types**: Strength, Toning/Endurance, Cardio, Flexibility, Rehab
- **4 muscle groups** with **17 specific muscles** for granular control
- **11 equipment types** for home and gym
- **9 API endpoints** for easy data access
- **Django admin interface** for manual data entry
- **Injury tracking** to exclude unsafe exercises
- **Equipment profiles** per user

## Quick Setup

Database is already populated! Just run the app:

```bash
cd fitness_ai_app
./setup_and_run.sh
```

Access admin at: `http://localhost:8000/admin`

## Admin Credentials

If needed, create a superuser:
```bash
python3 manage.py createsuperuser
```

## Database Contents

### Exercise Types
| Name | Exercises | Focus |
|------|-----------|-------|
| Strength | 9 | Maximum strength and muscle building |
| Toning/Endurance | 2 | Muscular endurance and tone |
| Cardio | 3 | Heart health and fat burning |
| Flexibility | 2 | Range of motion and recovery |
| Rehab | 2 | Injury recovery |

### Muscle Groups
- Upper Body (Arms, Shoulders, Chest, Back)
- Lower Body (Legs, Glutes, Hips)
- Core (Abs, Back, Stabilizers)
- Full Body (Compound movements)

### Sample Exercises

**Strength:**
1. Barbell Bench Press (Intermediate, Gym)
2. Pull-ups (Advanced, Gym)
3. Barbell Back Squat (Advanced, Gym)
4. Dumbbell Curl (Beginner, Both)
5. Romanian Deadlift (Intermediate, Gym)
6. Barbell Deadlift (Advanced, Gym)
7. Tricep Dips (Intermediate, Gym)
8. Dumbbell Lunges (Intermediate, Both)
9. Plank (Beginner, Both)

**Cardio:**
- Running (Intermediate, Both)
- Cycling (Beginner, Gym)
- Rowing (Intermediate, Gym)

**Flexibility:**
- Yoga (Beginner, Both)
- Foam Rolling (Beginner, Both)

**Endurance:**
- Push-ups (Beginner, Both)
- HIIT (Advanced, Both)

**Rehab:**
- Shoulder Rehabilitation (Beginner, Both)
- Knee Strengthening (Beginner, Both)

## API Reference

### Get All Exercise Types
```bash
GET /api/exercises/types/
```

### Filter Exercises
```bash
# Strength exercises at gym
GET /api/exercises/filter/?exercise_type=4&location=gym

# Beginner exercises
GET /api/exercises/filter/?difficulty=beginner

# Exercises for upper body
GET /api/exercises/filter/?muscle_group=1

# Cardio with equipment at home
GET /api/exercises/filter/?exercise_type=1&location=home&equipment=8

# Exclude injured muscles
GET /api/exercises/filter/?exclude_injured=true
```

### Get Safe Exercises (for current user)
```bash
# Gets exercises user can do based on injuries and equipment
GET /api/exercises/safe/?location=gym
```

### Record User Injury
```bash
POST /api/user/injury/add/
Content-Type: application/json

{
  "muscle_id": 5,
  "severity": "moderate",
  "notes": "Injured during training"
}
```

### Update User Equipment
```bash
POST /api/user/equipment/
Content-Type: application/json

{
  "location": "gym",
  "equipment": [1, 2, 3, 6]
}
```

## Admin Panel Guide

### Managing Exercises

1. **Add New Exercise**
   - Go to `/admin/core/trainingexercise/`
   - Click "Add Training Exercise"
   - Fill in all fields (see form for details)
   - Select related muscles and equipment
   - Save

2. **Edit Exercise**
   - Find in list
   - Click to open
   - Make changes
   - Save

3. **Key Fields**
   - **Name**: Exercise name (unique)
   - **Description**: What the exercise does
   - **Instructions**: Step-by-step guide
   - **Exercise Type**: Choose from 5 types
   - **Difficulty**: Beginner, Intermediate, Advanced
   - **Muscle Groups**: Select 1+ muscle groups
   - **Primary Muscles**: Main muscles targeted
   - **Secondary Muscles**: Supporting muscles
   - **Location**: Home, Gym, or Both
   - **Equipment**: Select required equipment
   - **Default Sets**: Recommended sets (e.g., 3)
   - **Default Reps**: Recommended reps (e.g., 10)
   - **High Impact**: Mark if high-impact (bad for some injuries)
   - **Joint Stress**: Text description (e.g., "knees, ankles")

### Managing Muscles

1. Go to `/admin/core/muscle/`
2. Add muscles to organized by muscle group
3. Use these for exercises and injury tracking

### Managing User Injuries

1. Go to `/admin/core/userinjury/`
2. Select user and affected muscle
3. Set severity: Mild, Moderate, Severe
4. Add start date (and end date if recovered)
5. Mark as active/inactive

### Managing Equipment Profiles

1. Go to `/admin/core/userequipmentprofile/`
2. View/edit equipment available to each user
3. Set location (Home, Gym, Both)
4. Select available equipment

## Frontend Integration Example

### React Component

```jsx
import React, { useState, useEffect } from 'react';

function ExerciseFilter() {
  const [exercises, setExercises] = useState([]);
  const [types, setTypes] = useState([]);
  const [selectedType, setSelectedType] = useState('');

  useEffect(() => {
    // Load exercise types
    fetch('/api/exercises/types/')
      .then(res => res.json())
      .then(data => setTypes(data.exercise_types));
  }, []);

  const filterExercises = async (typeId) => {
    const url = typeId 
      ? `/api/exercises/filter/?exercise_type=${typeId}`
      : '/api/exercises/filter/';
    
    const res = await fetch(url);
    const data = await res.json();
    setExercises(data.exercises);
  };

  return (
    <div>
      <select onChange={(e) => {
        setSelectedType(e.target.value);
        filterExercises(e.target.value);
      }}>
        <option value="">All Types</option>
        {types.map(t => (
          <option key={t.id} value={t.id}>{t.name}</option>
        ))}
      </select>

      <div className="exercises">
        {exercises.map(ex => (
          <div key={ex.id} className="exercise-card">
            <h3>{ex.name}</h3>
            <p>{ex.description}</p>
            <p>Difficulty: {ex.difficulty}</p>
            <p>Muscles: {ex.primary_muscles.map(m => m.name).join(', ')}</p>
            <p>Sets: {ex.default_sets} × Reps: {ex.default_reps}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default ExerciseFilter;
```

## Database Queries (Python)

### Get all strength exercises
```python
from core.models import TrainingExercise

strength = TrainingExercise.objects.filter(
    exercise_type__name='Strength'
)
```

### Get exercises for specific muscle
```python
bicep_exercises = TrainingExercise.objects.filter(
    primary_muscles__name='Biceps'
)
```

### Find exercises user can do (excluding injuries)
```python
from core.models import UserInjury

injured_muscles = UserInjury.objects.filter(
    user=user, 
    is_active=True
).values_list('muscle_id', flat=True)

safe_exercises = TrainingExercise.objects.exclude(
    primary_muscles__in=injured_muscles
).exclude(
    secondary_muscles__in=injured_muscles
)
```

### Get gym-only exercises with dumbbells
```python
TrainingExercise.objects.filter(
    location='gym',
    equipment__name='Dumbbells'
)
```

## Adding More Exercises

### Via Admin Panel
1. Go to `/admin/core/trainingexercise/`
2. Click "Add Training Exercise"
3. Fill form completely
4. Save

### Via Management Command
Edit `/fitness_ai_app/core/management/commands/populate_exercise_db.py`:
1. Add exercise data to `exercises_data` list
2. Run: `python manage.py populate_exercise_db`

### Via Django Shell
```python
from core.models import TrainingExercise, ExerciseType, Equipment, Muscle

exercise = TrainingExercise.objects.create(
    name='Lat Pulldown',
    description='Compound pulling exercise for back',
    instructions='1. Sit at machine...',
    exercise_type=ExerciseType.objects.get(name='Strength'),
    difficulty='intermediate',
    location='gym',
    default_sets=3,
    default_reps=8,
)

# Add relationships
exercise.muscle_groups.add(1)  # Upper Body
exercise.primary_muscles.add(7)  # Lats
exercise.equipment.add(3)  # Add equipment
```

## Statistics

```
Total Exercises: 18
Exercise Types: 5
Muscle Groups: 4
Specific Muscles: 17
Equipment Types: 11
API Endpoints: 9
```

## Troubleshooting

### No exercises showing in filter?
- Check `is_active` field is True
- Verify exercise_type relationship
- Check location filter matches

### Exercises appearing for inactive users?
- Verify `is_active=True` in admin

### Equipment not filtering correctly?
- Ensure user's `UserEquipmentProfile` is set up
- Check equipment IDs are correct

## Performance Notes

- Database includes indexes on `exercise_type` and `difficulty`
- Queries use `select_related()` for foreign keys
- `prefetch_related()` for many-to-many relationships
- All exercises cached by Django ORM

## Next Steps

1. **Add more exercises** via admin panel
2. **Create workout templates** combining exercises
3. **Add video URLs** to exercises
4. **Implement progress tracking**
5. **Add user ratings/reviews**
6. **Create AI recommendations** based on user data
7. **Integrate with fitness trackers** (Apple Health, Fitbit, etc.)

## Support

For issues or questions:
1. Check Django admin to verify data
2. Test API endpoints directly
3. Review `EXERCISE_DATABASE.md` for full documentation
4. Check model definitions in `core/models.py`
