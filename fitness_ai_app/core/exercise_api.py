"""
Exercise Database API Views
Provides filtering and querying for the comprehensive exercise database
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Prefetch
from django.utils import timezone
import json

from .models import (
    TrainingExercise, ExerciseType, MuscleGroup, Muscle, Equipment,
    UserInjury, UserEquipmentProfile
)


@require_http_methods(["GET"])
def get_exercise_types(request):
    """Get all available exercise types"""
    types = ExerciseType.objects.all().values('id', 'name', 'description')
    return JsonResponse({'exercise_types': list(types)})


@require_http_methods(["GET"])
def get_muscle_groups(request):
    """Get all available muscle groups"""
    groups = MuscleGroup.objects.all().values('id', 'name', 'description')
    return JsonResponse({'muscle_groups': list(groups)})


@require_http_methods(["GET"])
def get_muscles(request):
    """Get all available muscles, optionally filtered by muscle group"""
    muscle_group_id = request.GET.get('group_id')
    
    query = Muscle.objects.select_related('muscle_group')
    if muscle_group_id:
        query = query.filter(muscle_group_id=muscle_group_id)
    
    muscles = query.values('id', 'name', 'muscle_group__name', 'description')
    return JsonResponse({'muscles': list(muscles)})


@require_http_methods(["GET"])
def get_equipment(request):
    """Get all available equipment"""
    equipment = Equipment.objects.all().values('id', 'name', 'description')
    return JsonResponse({'equipment': list(equipment)})


@require_http_methods(["GET"])
@login_required
def filter_exercises(request):
    """
    Comprehensive exercise filtering endpoint
    
    Query Parameters:
    - exercise_type: ID of exercise type (Strength, Cardio, etc.)
    - muscle_group: ID of muscle group (Upper Body, Lower Body, etc.)
    - muscle: ID of specific muscle (Triceps, Biceps, etc.)
    - equipment: Comma-separated equipment IDs
    - location: 'home', 'gym', or 'both'
    - difficulty: 'beginner', 'intermediate', 'advanced'
    - exclude_injured: 'true' to exclude exercises affecting injured muscles
    """
    
    exercises = TrainingExercise.objects.filter(is_active=True).prefetch_related(
        'exercise_type',
        'muscle_groups',
        'primary_muscles',
        'secondary_muscles',
        'equipment'
    )
    
    # Filter by exercise type
    exercise_type_id = request.GET.get('exercise_type')
    if exercise_type_id:
        exercises = exercises.filter(exercise_type_id=exercise_type_id)
    
    # Filter by muscle group
    muscle_group_id = request.GET.get('muscle_group')
    if muscle_group_id:
        exercises = exercises.filter(muscle_groups__id=muscle_group_id).distinct()
    
    # Filter by specific muscle
    muscle_id = request.GET.get('muscle')
    if muscle_id:
        exercises = exercises.filter(
            Q(primary_muscles__id=muscle_id) | Q(secondary_muscles__id=muscle_id)
        ).distinct()
    
    # Filter by location
    location = request.GET.get('location')
    if location in ['home', 'gym']:
        exercises = exercises.filter(Q(location=location) | Q(location='both'))
    elif location == 'both':
        exercises = exercises.filter(location='both')
    
    # Filter by difficulty
    difficulty = request.GET.get('difficulty')
    if difficulty in ['beginner', 'intermediate', 'advanced']:
        exercises = exercises.filter(difficulty=difficulty)
    
    # Filter by equipment (user has at least one of these)
    equipment_ids = request.GET.get('equipment')
    if equipment_ids:
        equipment_list = [int(x) for x in equipment_ids.split(',') if x.isdigit()]
        exercises = exercises.filter(equipment__id__in=equipment_list).distinct()
    
    # Exclude exercises affecting injured muscles
    exclude_injured = request.GET.get('exclude_injured', 'false').lower() == 'true'
    if exclude_injured:
        user_injuries = UserInjury.objects.filter(
            user=request.user,
            is_active=True
        ).values_list('muscle_id', flat=True)
        
        exercises = exercises.exclude(
            Q(primary_muscles__id__in=user_injuries) |
            Q(secondary_muscles__id__in=user_injuries)
        ).distinct()
    
    # Serialize response
    exercise_list = []
    for exercise in exercises:
        exercise_list.append({
            'id': exercise.id,
            'name': exercise.name,
            'description': exercise.description,
            'instructions': exercise.instructions,
            'difficulty': exercise.get_difficulty_display(),
            'exercise_type': {
                'id': exercise.exercise_type.id,
                'name': exercise.exercise_type.name,
            },
            'muscle_groups': [
                {'id': mg.id, 'name': mg.name}
                for mg in exercise.muscle_groups.all()
            ],
            'primary_muscles': [
                {'id': m.id, 'name': m.name}
                for m in exercise.primary_muscles.all()
            ],
            'secondary_muscles': [
                {'id': m.id, 'name': m.name}
                for m in exercise.secondary_muscles.all()
            ],
            'location': exercise.get_location_display(),
            'equipment': [
                {'id': e.id, 'name': e.name}
                for e in exercise.equipment.all()
            ],
            'default_sets': exercise.default_sets,
            'default_reps': exercise.default_reps,
            'default_duration_seconds': exercise.default_duration_seconds,
            'high_impact': exercise.high_impact,
            'joint_stress': exercise.joint_stress,
        })
    
    return JsonResponse({
        'count': len(exercise_list),
        'exercises': exercise_list
    })


@require_http_methods(["GET"])
@login_required
def get_user_safe_exercises(request):
    """
    Get exercises safe for the current user based on injuries and equipment
    
    Query Parameters:
    - exercise_type: ID of exercise type (optional)
    - muscle_group: ID of muscle group (optional)
    - location: 'home' or 'gym' (required for filtering equipment)
    """
    
    location = request.GET.get('location', 'gym')
    
    # Get user's equipment profile
    try:
        user_equipment = UserEquipmentProfile.objects.get(user=request.user)
        available_equipment = list(user_equipment.equipment.values_list('id', flat=True))
    except UserEquipmentProfile.DoesNotExist:
        available_equipment = []
    
    # Get user's active injuries
    user_injuries = UserInjury.objects.filter(
        user=request.user,
        is_active=True
    ).values_list('muscle_id', flat=True)
    
    # Build filter params
    params = {
        'exclude_injured': 'true',
        'location': location,
    }
    
    if available_equipment:
        params['equipment'] = ','.join(map(str, available_equipment))
    
    exercise_type_id = request.GET.get('exercise_type')
    if exercise_type_id:
        params['exercise_type'] = exercise_type_id
    
    muscle_group_id = request.GET.get('muscle_group')
    if muscle_group_id:
        params['muscle_group'] = muscle_group_id
    
    # Call filter_exercises with user context
    request.GET = request.GET.copy()
    for key, value in params.items():
        request.GET[key] = value
    
    return filter_exercises(request)


@require_http_methods(["GET"])
def get_exercise_detail(request, exercise_id):
    """Get detailed information about a specific exercise"""
    try:
        exercise = TrainingExercise.objects.prefetch_related(
            'exercise_type',
            'muscle_groups',
            'primary_muscles',
            'secondary_muscles',
            'equipment'
        ).get(id=exercise_id, is_active=True)
        
        return JsonResponse({
            'id': exercise.id,
            'name': exercise.name,
            'description': exercise.description,
            'instructions': exercise.instructions,
            'difficulty': exercise.get_difficulty_display(),
            'exercise_type': {
                'id': exercise.exercise_type.id,
                'name': exercise.exercise_type.name,
                'description': exercise.exercise_type.description,
            },
            'muscle_groups': [
                {'id': mg.id, 'name': mg.name}
                for mg in exercise.muscle_groups.all()
            ],
            'primary_muscles': [
                {'id': m.id, 'name': m.name}
                for m in exercise.primary_muscles.all()
            ],
            'secondary_muscles': [
                {'id': m.id, 'name': m.name}
                for m in exercise.secondary_muscles.all()
            ],
            'location': exercise.get_location_display(),
            'equipment': [
                {'id': e.id, 'name': e.name}
                for e in exercise.equipment.all()
            ],
            'default_sets': exercise.default_sets,
            'default_reps': exercise.default_reps,
            'default_duration_seconds': exercise.default_duration_seconds,
            'high_impact': exercise.high_impact,
            'joint_stress': exercise.joint_stress,
        })
    except TrainingExercise.DoesNotExist:
        return JsonResponse({'error': 'Exercise not found'}, status=404)


@require_http_methods(["POST"])
@login_required
def add_user_injury(request):
    """Add an injury to user's profile"""
    try:
        data = json.loads(request.body)
        muscle_id = data.get('muscle_id')
        severity = data.get('severity', 'moderate')
        notes = data.get('notes', '')
        
        injury = UserInjury.objects.create(
            user=request.user,
            muscle_id=muscle_id,
            severity=severity,
            notes=notes,
            start_date=timezone.now().date()
        )
        
        return JsonResponse({
            'success': True,
            'injury_id': injury.id,
            'message': 'Injury recorded successfully'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["POST"])
@login_required
def update_user_equipment(request):
    """Update user's available equipment"""
    try:
        data = json.loads(request.body)
        location = data.get('location', 'gym')
        equipment_ids = data.get('equipment', [])
        
        profile, created = UserEquipmentProfile.objects.get_or_create(user=request.user)
        profile.location = location
        profile.save()
        profile.equipment.set(equipment_ids)
        
        return JsonResponse({
            'success': True,
            'message': 'Equipment profile updated'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
