import json
import os
import time
import random

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from openai import OpenAI
import logging
import smtplib
from datetime import datetime, date, timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.conf import settings
from django.db import transaction
from django.db.models import Q, Sum
from django.urls import reverse

from .forms import RegistrationForm, ForgotPasswordForm, ResetPasswordForm
from .models import (
    Meal,
    FoodItem,
    FoodGroup,
    Workout,
    Exercise,
    PasswordReset,
    UserProfile,
    SupplementDatabase,
    SupplementEntry,
    MealSupplement,
    ExerciseType,
    MuscleGroup,
    Muscle,
    Equipment,
    TrainingExercise,
)


def get_user_calorie_goal(user, default=2400):
    """
    Fetch the user's calorie goal from their profile, or return default if not set.
    """
    try:
        profile = UserProfile.objects.get(user=user)
        return profile.calorie_goal or default
    except UserProfile.DoesNotExist:
        return default


def get_default_workout_goal(user):
    """Map onboarding primary goal to train-page workout goal defaults."""
    try:
        user_primary_goal = user.profile.primary_goal
    except UserProfile.DoesNotExist:
        return ''

    valid_workout_goals = {choice_value for choice_value, _ in Workout.GOAL_CHOICES}
    return user_primary_goal if user_primary_goal in valid_workout_goals else ''


def _parse_optional_positive_int(raw_value, field_label):
    """Parse optional positive integer form fields with user-friendly errors."""
    if raw_value in (None, ''):
        return None, None

    try:
        parsed = int(raw_value)
    except (TypeError, ValueError):
        return None, f'{field_label} must be a whole number.'

    if parsed < 0:
        return None, f'{field_label} cannot be negative.'

    return parsed, None


def _infer_muscle_group_from_training_exercise(training_exercise):
    """Map a TrainingExercise to legacy Exercise muscle groups."""
    keyword_map = {
        'arms': ('bicep', 'tricep', 'forearm'),
        'chest': ('chest', 'pec'),
        'back': ('back', 'lat'),
        'shoulders': ('shoulder', 'deltoid'),
        'legs': ('quad', 'hamstring', 'glute', 'calf', 'hip', 'adductor'),
        'core': ('abs', 'oblique', 'core', 'abdominis'),
    }

    muscle_names = [
        muscle.name.lower()
        for muscle in training_exercise.primary_muscles.all()
    ] + [
        muscle.name.lower()
        for muscle in training_exercise.secondary_muscles.all()
    ]

    for group_key, keywords in keyword_map.items():
        if any(keyword in muscle_name for keyword in keywords for muscle_name in muscle_names):
            return group_key

    muscle_group_names = [group.name.lower() for group in training_exercise.muscle_groups.all()]
    if any('core' in name for name in muscle_group_names):
        return 'core'
    if any(('lower' in name) or ('leg' in name) for name in muscle_group_names):
        return 'legs'
    if any('upper' in name for name in muscle_group_names):
        return 'chest'

    return 'core'


def splash(request):
    if request.user.is_authenticated:
        return redirect('home_dash')
    return render(request, 'core/splash.html')


@login_required
def chat_page(request):
    return render(request, 'core/chat.html', {'active_tab': 'ai'})


@csrf_exempt
@require_http_methods(["POST"])
def api_chat(request):
    try:
        body = json.loads(request.body)
        messages = body.get("messages", [])
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    if not messages:
        return JsonResponse({"error": "messages list is required."}, status=400)

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return JsonResponse({"error": "OPENAI_API_KEY not configured."}, status=500)

    client = OpenAI(api_key=api_key)

    system_prompt = {
        "role": "system",
        "content": (
            "You are an AI chatbot for a fitness app called Spotter.ai. "
            "Only discuss health, food, and fitness with the user. "
            "If the user asks about anything else, politely redirect them "
            "back to health, food, or fitness topics. "
            "Keep your responses short — no more than 2-3 sentences for usability."
        ),
    }

    try:
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=messages,
        )
        reply = response.choices[0].message.content
        return JsonResponse({"reply": reply})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=502)

from django.core.mail import send_mail
from .models import EmailVerification

logger = logging.getLogger(__name__)

def user_get_started(request):
    if request.user.is_authenticated:
        return redirect('home_dash')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                    logger.info(f'User created: {user.username}, is_active={user.is_active}')

                    if settings.EMAIL_VERIFICATION_ENABLED:
                        # Email verification is enabled - user must verify before login
                        verification = EmailVerification.objects.create(user=user)
                        logger.info(f'Verification created for {user.username} with token {verification.token}')

                        verify_url = request.build_absolute_uri(f'/verify_email/{verification.token}/')
                        logger.info(f'Verify URL: {verify_url}')

                        html_message = f"""
                        <div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;padding:32px;background:#111;border-radius:16px;">
                            <h1 style="color:#F67D26;text-align:center;">Spotter.ai</h1>
                            <p style="color:#fff;font-size:1.1rem;text-align:center;">Welcome! Click the button below to verify your email and activate your account.</p>
                            <div style="text-align:center;margin:32px 0;">
                                <a href="{verify_url}" style="display:inline-block;padding:16px 48px;background:#F67D26;color:#fff;font-size:1.1rem;font-weight:600;border-radius:12px;text-decoration:none;">Verify My Email</a>
                            </div>
                            <p style="color:rgba(255,255,255,0.5);font-size:0.85rem;text-align:center;">This link expires in 24 hours. If you didn't create an account, you can ignore this email.</p>
                        </div>
                        """

                        logger.info(f'Sending verification email to {user.email} from {settings.DEFAULT_FROM_EMAIL}')
                        result = send_mail(
                            'Verify your Spotter.ai account',
                            f'Click this link to verify your account: {verify_url}',
                            settings.DEFAULT_FROM_EMAIL,
                            [user.email],
                            html_message=html_message,
                            fail_silently=False,
                        )
                        logger.info(f'Email sent successfully! Result: {result}')
                        messages.success(request, 'Account created! Please check your email to verify.')
                    else:
                        # Email verification is disabled - auto-activate user for testing
                        user.is_active = True
                        user.save()
                        verification = EmailVerification.objects.create(user=user, verified=True)
                        logger.info(f'Email verification disabled - user auto-activated: {user.username}')
                        messages.success(request, 'Account created successfully! You can now log in.')
            except Exception as e:
                logger.exception(f'Failed during signup for {form.cleaned_data.get("email")}')
                form.add_error(None, 'We could not create your account right now.')
                return render(request, 'core/user_get_started.html', {'form': form})

            return redirect('user_login')
        else:
            return render(request, 'core/user_get_started.html', {'form': form})

    form = RegistrationForm()
    return render(request, 'core/user_get_started.html', {'form': form})


@login_required
def get_started_profile(request):
    if request.method == 'POST':
        # Update user profile information
        user = request.user
        user.first_name = request.POST.get('name', user.first_name)
        user.save()
        
        # Update or create user profile with fitness metrics
        from core.models import UserProfile
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        # Save calorie goal
        calorie_goal = request.POST.get('calorie_goal', '').strip()
        if calorie_goal:
            try:
                profile.calorie_goal = int(calorie_goal)
            except (ValueError, TypeError):
                pass
        
        # Save height
        height = request.POST.get('height', '').strip()
        if height:
            try:
                profile.height = int(height)
            except (ValueError, TypeError):
                pass
        
        # Save weight
        weight = request.POST.get('weight', '').strip()
        if weight:
            try:
                profile.weight = int(weight)
            except (ValueError, TypeError):
                pass
        
        # Save age
        age = request.POST.get('age', '').strip()
        if age:
            try:
                profile.age = int(age)
            except (ValueError, TypeError):
                pass
        
        # Save primary goal
        primary_goal = request.POST.get('primary_goal', '').strip()
        if primary_goal:
            profile.primary_goal = primary_goal
        
        # Save experience level
        experience_level = request.POST.get('experience_level', '').strip()
        if experience_level:
            profile.experience_level = experience_level
        
        # Save dietary preference
        dietary_preference = request.POST.get('dietary_preference', '').strip()
        if dietary_preference:
            profile.dietary_preference = dietary_preference
        
        # Save home gym status
        has_home_gym = request.POST.get('has_home_gym', '').strip()
        if has_home_gym:
            profile.has_home_gym = has_home_gym == 'yes'
        
        # Save home equipment (multiple selections)
        home_equipment = request.POST.getlist('home_equipment')
        profile.home_equipment = [eq for eq in home_equipment if eq]
        
        # Save bio
        bio = request.POST.get('bio', '').strip()
        if bio:
            profile.bio = bio
        else:
            profile.bio = None
        
        # Mark onboarding as completed
        profile.onboarding_completed = True
        profile.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('home_dash')
    
    # Handle GET request with skip parameter
    if request.GET.get('skip') == 'true':
        from core.models import UserProfile
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        profile.onboarding_completed = True
        profile.save()
        return redirect('home_dash')
    
    # GET request - pass profile data to template
    from core.models import UserProfile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Show skip button on first-time onboarding (any user who hasn't completed it yet)
    is_first_time_onboarding = not profile.onboarding_completed
    
    return render(request, 'profile_dir/get_started_profile.html', {
        'active_tab': 'profile',
        'profile': profile,
        'is_first_time_onboarding': is_first_time_onboarding
    })


def verify_email(request, token):
    try:
        verification = EmailVerification.objects.get(token=token)
    except EmailVerification.DoesNotExist:
        messages.error(request, 'Invalid verification link.')
        return redirect('user_login')

    if verification.verified:
        messages.info(request, 'Your account is already verified. Please log in.')
        return redirect('user_login')

    if verification.is_expired():
        messages.error(request, 'Verification link has expired. Please sign up again.')
        verification.user.delete()
        return redirect('user_get_started')

    verification.verified = True
    verification.save()
    verification.user.is_active = True
    verification.user.save()
    login(request, verification.user, backend='django.contrib.auth.backends.ModelBackend')
    messages.success(request, 'Your email has been verified! Welcome to Spotter.ai.')
    return redirect('get_started_profile')


def user_login(request):
    if request.user.is_authenticated:
        return redirect('home_dash')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'home_dash')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid email or password.')

    return render(request, 'core/user_login.html')


def forgot_password(request):
    if request.user.is_authenticated:
        return redirect('home_dash')

    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            start_time = time.time()
            
            # Case-insensitive lookup on both email and username fields
            user = User.objects.filter(Q(email__iexact=email) | Q(username__iexact=email)).first()
            
            if user:
                try:
                    # Create password reset token
                    reset = PasswordReset.objects.create(user=user)
                    reset_url = request.build_absolute_uri(f'/reset_password/{reset.token}/')
                    
                    # Send reset email
                    html_message = f"""
                    <div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;padding:32px;background:#111;border-radius:16px;">
                        <h1 style="color:#F67D26;text-align:center;">Spotter.ai</h1>
                        <p style="color:#fff;font-size:1.1rem;text-align:center;">Click the button below to reset your password.</p>
                        <div style="text-align:center;margin:32px 0;">
                            <a href="{reset_url}" style="display:inline-block;padding:16px 48px;background:#F67D26;color:#fff;font-size:1.1rem;font-weight:600;border-radius:12px;text-decoration:none;">Reset Password</a>
                        </div>
                        <p style="color:rgba(255,255,255,0.5);font-size:0.85rem;text-align:center;">This link expires in 24 hours. If you didn't request a password reset, you can ignore this email.</p>
                    </div>
                    """
                    
                    send_mail(
                        'Reset your Spotter.ai password',
                        f'Click this link to reset your password: {reset_url}',
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        html_message=html_message,
                        fail_silently=False,
                    )
                except Exception as e:
                    logger.error(f'Failed to send password reset email to {user.email}: {str(e)}')
            
            # Random delay between 0.5 and 3 seconds to prevent timing attacks
            elapsed = time.time() - start_time
            target_delay = random.uniform(0.5, 2.0)
            if elapsed < target_delay:
                time.sleep(target_delay - elapsed)
            
            messages.success(request, 'If an account exists with that email, you will receive a password reset link.')
            return redirect('user_login')
    else:
        form = ForgotPasswordForm()

    return render(request, 'core/forgot_password.html', {'form': form})


def reset_password(request, token):
    try:
        reset = PasswordReset.objects.get(token=token)
    except PasswordReset.DoesNotExist:
        # Show error on template instead of redirecting
        return render(request, 'core/reset_password.html', {
            'form': ResetPasswordForm(),
            'error_message': 'Invalid or expired reset link. Please request a new one.'
        })

    if reset.used:
        return render(request, 'core/reset_password.html', {
            'form': ResetPasswordForm(),
            'error_message': 'Invalid or expired reset link. Please request a new one.'
        })

    if reset.is_expired():
        return render(request, 'core/reset_password.html', {
            'form': ResetPasswordForm(),
            'error_message': 'Invalid or expired reset link. Please request a new one.'
        })

    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data['password']
            user = reset.user
            user.set_password(password)
            user.save()
            
            reset.used = True
            reset.save()
            
            messages.success(request, 'Your password has been reset. You can now log in.')
            return redirect('user_login')
    else:
        form = ResetPasswordForm()

    return render(request, 'core/reset_password.html', {'form': form})


def user_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('splash')


@login_required
def home_dash(request):
    # Redirect to onboarding if social login user hasn't completed it
    try:
        profile = request.user.profile
        if profile.social_login_user and not profile.onboarding_completed:
            return redirect('get_started_profile')
    except:
        pass
    
    # Check for discard action from profile
    if request.GET.get('discard') == 'true':
        messages.info(request, 'Changes discarded. Nothing was saved.')
    
    today = date.today()
    total_calories = FoodItem.objects.filter(
        meal__user=request.user,
        meal__date=today,
        completed=True
    ).aggregate(total=Sum('calories'))['total'] or 0
    
    # Get calorie goal from user profile or use default
    calorie_goal = get_user_calorie_goal(request.user)
    
    calories_percentage = (total_calories / calorie_goal) * 100 if calorie_goal > 0 else 0
    workout_goal = 5
    completed_exercises = Exercise.objects.filter(
        workout__user=request.user,
        workout__date=today,
        completed=True,
    ).count()
    workout_goal_percentage = (completed_exercises / workout_goal) * 100 if workout_goal > 0 else 0
    
    return render(request, 'home_dash_dir/home_dash.html', {
        'active_tab': 'home',
        'total_calories': total_calories,
        'calorie_goal': calorie_goal,
        'calories_percentage': calories_percentage,
        'workout_goal': workout_goal,
        'completed_exercises': completed_exercises,
        'workout_goal_percentage': workout_goal_percentage,
    })


@login_required
def train_page(request):
    date_param = request.GET.get('date')
    if date_param:
        try:
            selected_date = datetime.strptime(date_param, '%Y-%m-%d').date()
        except ValueError:
            selected_date = date.today()
    else:
        selected_date = date.today()

    selected_tab = request.GET.get('tab', 'today')
    if selected_tab not in {'today', 'history', 'search'}:
        selected_tab = 'today'

    workouts = (
        Workout.objects.filter(user=request.user, date=selected_date)
        .prefetch_related('exercises')
    )
    history_workouts = (
        Workout.objects.filter(user=request.user, date__lt=selected_date)
        .prefetch_related('exercises')
        .order_by('-date', '-created_at')[:20]
    )

    exercise_types = list(ExerciseType.objects.all().values('id', 'name'))
    muscle_groups = list(MuscleGroup.objects.all().values('id', 'name'))
    muscles = list(
        Muscle.objects.select_related('muscle_group').all().values(
            'id',
            'name',
            'muscle_group_id',
            'muscle_group__name',
        )
    )
    equipment_options = list(Equipment.objects.all().values('id', 'name'))
    exercise_database_count = TrainingExercise.objects.filter(is_active=True).count()
    default_workout_goal = get_default_workout_goal(request.user)
    workout_goal_choices = Workout.GOAL_CHOICES

    prev_date = (selected_date - timedelta(days=1)).strftime('%Y-%m-%d')
    next_date = (selected_date + timedelta(days=1)).strftime('%Y-%m-%d')
    is_past_date = selected_date < date.today()

    context = {
        'active_tab': 'train',
        'selected_date': selected_date,
        'date_string': selected_date.strftime('%Y-%m-%d'),
        'prev_date': prev_date,
        'next_date': next_date,
        'workouts': workouts,
        'history_workouts': history_workouts,
        'is_past_date': is_past_date,
        'selected_tab': selected_tab,
        'exercise_types': exercise_types,
        'muscle_groups': muscle_groups,
        'muscles': muscles,
        'equipment_options': equipment_options,
        'exercise_database_count': exercise_database_count,
        'default_workout_goal': default_workout_goal,
        'workout_goal_choices': workout_goal_choices,
    }
    return render(request, 'train_dir/train_page.html', context)


@login_required
@require_POST
def add_workout(request):
    workout_name = request.POST.get('workout_name', '').strip()
    goal = request.POST.get('goal', '').strip()
    status = request.POST.get('status', 'planned').strip()
    date_param = request.POST.get('date')

    if not workout_name or not goal or not date_param:
        messages.error(request, 'Workout name, goal, and date are required.')
        return redirect(f"{reverse('train_page')}?date={date_param}" if date_param else reverse('train_page'))

    try:
        workout_date = datetime.strptime(date_param, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, 'Invalid date format.')
        return redirect(reverse('train_page'))

    Workout.objects.create(user=request.user, name=workout_name, goal=goal, status=status, date=workout_date)
    return redirect(f"{reverse('train_page')}?date={date_param}")


@login_required
@require_POST
def delete_workout(request):
    workout_id = request.POST.get('workout_id')
    date_param = request.POST.get('date')

    workout = get_object_or_404(Workout, id=workout_id, user=request.user)
    workout.delete()

    return redirect(f"{reverse('train_page')}?date={date_param}" if date_param else reverse('train_page'))


@login_required
@require_POST
def add_exercise(request):
    workout_id = request.POST.get('workout_id')
    exercise_name = request.POST.get('exercise_name', '').strip()
    muscle_group = request.POST.get('muscle_group', '').strip()
    training_exercise_id = request.POST.get('training_exercise_id', '').strip()
    sets = request.POST.get('sets', '').strip()
    reps = request.POST.get('reps', '').strip()
    weight = request.POST.get('weight', '').strip()
    status = request.POST.get('status', 'planned').strip()
    date_param = request.POST.get('date')
    tab_param = request.POST.get('tab', '').strip()

    base_redirect_url = f"{reverse('train_page')}?date={date_param}" if date_param else reverse('train_page')
    if tab_param:
        connector = '&' if '?' in base_redirect_url else '?'
        base_redirect_url = f"{base_redirect_url}{connector}tab={tab_param}"

    training_exercise = None
    if training_exercise_id:
        training_exercise = (
            TrainingExercise.objects.filter(id=training_exercise_id, is_active=True)
            .prefetch_related('muscle_groups', 'primary_muscles', 'secondary_muscles')
            .first()
        )
        if not training_exercise:
            messages.error(request, 'Selected exercise was not found in the exercise database.')
            return redirect(base_redirect_url)

    if training_exercise:
        if not exercise_name:
            exercise_name = training_exercise.name
        if not muscle_group:
            muscle_group = _infer_muscle_group_from_training_exercise(training_exercise)
        if not sets and training_exercise.default_sets:
            sets = str(training_exercise.default_sets)
        if not reps and training_exercise.default_reps:
            reps = str(training_exercise.default_reps)

    if not workout_id or not exercise_name or not muscle_group:
        messages.error(request, 'Exercise name and muscle group are required.')
        return redirect(base_redirect_url)

    workout = get_object_or_404(Workout, id=workout_id, user=request.user)
    sets_value, sets_error = _parse_optional_positive_int(sets, 'Sets')
    reps_value, reps_error = _parse_optional_positive_int(reps, 'Reps')
    weight_value, weight_error = _parse_optional_positive_int(weight, 'Weight')

    validation_error = sets_error or reps_error or weight_error
    if validation_error:
        messages.error(request, validation_error)
        return redirect(base_redirect_url)

    Exercise.objects.create(
        workout=workout,
        name=exercise_name,
        muscle_group=muscle_group,
        sets=sets_value,
        reps=reps_value,
        weight=weight_value,
        completed=(status == 'completed'),
    )
    return redirect(base_redirect_url)


@login_required
@require_POST
def edit_exercise(request):
    exercise_id = request.POST.get('exercise_id')
    exercise_name = request.POST.get('exercise_name', '').strip()
    muscle_group = request.POST.get('muscle_group', '').strip()
    sets = request.POST.get('sets', '').strip()
    reps = request.POST.get('reps', '').strip()
    weight = request.POST.get('weight', '').strip()
    status = request.POST.get('status', 'planned').strip()
    date_param = request.POST.get('date')

    if not exercise_id or not exercise_name or not muscle_group:
        messages.error(request, 'Exercise name and muscle group are required.')
        return redirect(f"{reverse('train_page')}?date={date_param}" if date_param else reverse('train_page'))

    exercise = get_object_or_404(Exercise, id=exercise_id, workout__user=request.user)
    sets_value, sets_error = _parse_optional_positive_int(sets, 'Sets')
    reps_value, reps_error = _parse_optional_positive_int(reps, 'Reps')
    weight_value, weight_error = _parse_optional_positive_int(weight, 'Weight')

    validation_error = sets_error or reps_error or weight_error
    if validation_error:
        messages.error(request, validation_error)
        return redirect(f"{reverse('train_page')}?date={date_param}" if date_param else reverse('train_page'))

    exercise.name = exercise_name
    exercise.muscle_group = muscle_group
    exercise.sets = sets_value
    exercise.reps = reps_value
    exercise.weight = weight_value
    exercise.completed = (status == 'completed')
    exercise.save()

    return redirect(f"{reverse('train_page')}?date={date_param}")


@login_required
@require_POST
def toggle_exercise(request):
    exercise_id = request.POST.get('exercise_id')
    date_param = request.POST.get('date')

    exercise = get_object_or_404(Exercise, id=exercise_id, workout__user=request.user)
    exercise.completed = not exercise.completed
    exercise.save()

    return redirect(f"{reverse('train_page')}?date={date_param}" if date_param else reverse('train_page'))


@login_required
@require_POST
def delete_exercise(request):
    exercise_id = request.POST.get('exercise_id')
    date_param = request.POST.get('date')

    exercise = get_object_or_404(Exercise, id=exercise_id, workout__user=request.user)
    exercise.delete()

    return redirect(f"{reverse('train_page')}?date={date_param}" if date_param else reverse('train_page'))


@login_required
def nutrition_page(request):
    date_param = request.GET.get('date')
    if date_param:
        try:
            selected_date = datetime.strptime(date_param, '%Y-%m-%d').date()
        except ValueError:
            selected_date = date.today()
    else:
        selected_date = date.today()

    meals = (
        Meal.objects.filter(user=request.user, date=selected_date)
        .prefetch_related('items', 'supplements')
        .annotate(meal_total=Sum('items__calories'))
    )

    # Get all completed food items for the day
    completed_items = FoodItem.objects.filter(
        meal__user=request.user,
        meal__date=selected_date,
        completed=True,
    )

    # Calculate totals
    totals = completed_items.aggregate(
        total_calories=Sum('calories'),
        total_protein=Sum('protein'),
        total_carbs=Sum('carbs'),
        total_fats=Sum('fats')
    )

    total_calories = totals['total_calories'] or 0
    total_protein = totals['total_protein'] or 0
    total_carbs = totals['total_carbs'] or 0
    total_fats = totals['total_fats'] or 0

    # Get calorie goal from user profile or use default
    calorie_goal = get_user_calorie_goal(request.user)
    
    calories_percentage = min(
        round(total_calories / calorie_goal * 100, 1) if calorie_goal else 0,
        100,
    )

    prev_date = (selected_date - timedelta(days=1)).strftime('%Y-%m-%d')
    next_date = (selected_date + timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Get supplements for the selected date
    supplements = SupplementEntry.objects.filter(user=request.user, date=selected_date).order_by('name')

    context = {
        'active_tab': 'nutrition',
        'meals': meals,
        'selected_date': selected_date,
        'date_string': selected_date.strftime('%Y-%m-%d'),
        'prev_date': prev_date,
        'next_date': next_date,
        'total_calories': total_calories,
        'total_protein': total_protein,
        'total_carbs': total_carbs,
        'total_fats': total_fats,
        'calorie_goal': calorie_goal,
        'calories_percentage': calories_percentage,
        'supplements': supplements,
    }
    return render(request, 'nutrition_dir/nutrition_page.html', context)


@login_required
@require_POST
def add_meal(request):
    date_param = request.POST.get('date')
    meal_name = request.POST.get('meal_name', '').strip()
    
    if not date_param:
        messages.error(request, 'Date is required.')
        return redirect(reverse('nutrition_page'))
    
    try:
        meal_date = datetime.strptime(date_param, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, 'Invalid date format.')
        return redirect(reverse('nutrition_page'))
    
    # If no meal name provided, auto-generate based on time of day
    if not meal_name:
        current_hour = datetime.now().hour
        if current_hour < 12:
            meal_name = 'Breakfast'
        elif current_hour < 17:
            meal_name = 'Lunch'
        else:
            meal_name = 'Dinner'
        
        # Check if this meal already exists for today, if so add a number
        existing_meals = Meal.objects.filter(user=request.user, date=meal_date, name=meal_name).count()
        if existing_meals > 0:
            meal_name = f'{meal_name} {existing_meals + 1}'
    
    Meal.objects.create(user=request.user, name=meal_name, date=meal_date)
    messages.success(request, f'Meal "{meal_name}" added successfully.')
    return redirect(f"{reverse('nutrition_page')}?date={date_param}")


@login_required
@require_POST
def add_food_item(request):
    meal_id = request.POST.get('meal_id')
    food_name = request.POST.get('food_name', '').strip()
    food_calories = request.POST.get('food_calories', '0')
    item_id = request.POST.get('item_id')  # For editing
    date_param = request.POST.get('date')
    
    if not meal_id or not food_name or not food_calories:
        messages.error(request, 'All fields are required.')
        return redirect(f"{reverse('nutrition_page')}?date={date_param}" if date_param else reverse('nutrition_page'))
    
    meal = get_object_or_404(Meal, id=meal_id, user=request.user)
    
    try:
        calories = int(food_calories)
    except ValueError:
        messages.error(request, 'Calories must be a number.')
        return redirect(f"{reverse('nutrition_page')}?date={date_param}")
    
    # Optional macro fields
    protein = request.POST.get('protein', '0')
    carbs = request.POST.get('carbs', '0')
    fats = request.POST.get('fats', '0')
    
    try:
        protein = int(protein) if protein else 0
        carbs = int(carbs) if carbs else 0
        fats = int(fats) if fats else 0
    except ValueError:
        protein = carbs = fats = 0
    
    # Check if this is an update or create
    if item_id:
        try:
            food_item = FoodItem.objects.get(id=item_id, meal__user=request.user)
            food_item.name = food_name
            food_item.calories = calories
            food_item.protein = protein
            food_item.carbs = carbs
            food_item.fats = fats
            food_item.save()
            messages.success(request, f'Food item "{food_name}" updated.')
        except FoodItem.DoesNotExist:
            messages.error(request, 'Food item not found.')
    else:
        FoodItem.objects.create(
            meal=meal,
            name=food_name,
            calories=calories,
            protein=protein,
            carbs=carbs,
            fats=fats
        )
        messages.success(request, f'Food item "{food_name}" added to {meal.name}.')

    return redirect(f"{reverse('nutrition_page')}?date={date_param}")


@login_required
@require_POST
def add_food_item_ajax(request):
    """JSON endpoint: add a food item to a meal without redirecting, for the
    continuous-add flow in the Create Meal modal."""
    meal_id = request.POST.get('meal_id')
    food_name = request.POST.get('food_name', '').strip()
    food_calories = request.POST.get('food_calories', '0')

    if not meal_id or not food_name or not food_calories:
        return JsonResponse({'error': 'All fields are required.'}, status=400)

    meal = get_object_or_404(Meal, id=meal_id, user=request.user)

    try:
        calories = int(food_calories)
    except ValueError:
        return JsonResponse({'error': 'Calories must be a number.'}, status=400)

    try:
        protein = int(request.POST.get('protein') or 0)
        carbs = int(request.POST.get('carbs') or 0)
        fats = int(request.POST.get('fats') or 0)
    except ValueError:
        protein = carbs = fats = 0

    group_id = request.POST.get('group_id')
    group = None
    if group_id:
        group = get_object_or_404(FoodGroup, id=group_id, meal__user=request.user)

    item = FoodItem.objects.create(
        meal=meal, name=food_name, calories=calories,
        protein=protein, carbs=carbs, fats=fats, group=group,
    )
    return JsonResponse({
        'item_id': item.id,
        'name': item.name,
        'calories': item.calories,
        'protein': item.protein,
        'carbs': item.carbs,
        'fats': item.fats,
    })


@login_required
@require_POST
def create_food_group_ajax(request):
    meal_id = request.POST.get('meal_id')
    name = (request.POST.get('name') or '').strip() or 'My Group'
    meal = get_object_or_404(Meal, id=meal_id, user=request.user)
    group = FoodGroup.objects.create(meal=meal, name=name)
    return JsonResponse({'group_id': group.id, 'name': group.name})


@login_required
@require_POST
def toggle_food_item(request):
    item_id = request.POST.get('item_id')
    date_param = request.POST.get('date')
    
    food_item = get_object_or_404(FoodItem, id=item_id, meal__user=request.user)
    food_item.completed = not food_item.completed
    food_item.save()
    
    return redirect(f"{reverse('nutrition_page')}?date={date_param}" if date_param else reverse('nutrition_page'))


@login_required
@require_POST
def delete_food_item(request):
    item_id = request.POST.get('item_id')
    date_param = request.POST.get('date')
    
    food_item = get_object_or_404(FoodItem, id=item_id, meal__user=request.user)
    food_item.delete()
    messages.success(request, 'Food item deleted.')
    
    return redirect(f"{reverse('nutrition_page')}?date={date_param}" if date_param else reverse('nutrition_page'))


@login_required
@require_POST
def delete_food_group(request):
    group_id = request.POST.get('group_id')
    date_param = request.POST.get('date')
    group = get_object_or_404(FoodGroup, id=group_id, meal__user=request.user)
    group.delete()
    messages.success(request, 'Group deleted.')
    return redirect(f"{reverse('nutrition_page')}?date={date_param}" if date_param else reverse('nutrition_page'))


@login_required
@require_POST
def delete_meal(request):
    meal_id = request.POST.get('meal_id')
    date_param = request.POST.get('date')
    
    meal = get_object_or_404(Meal, id=meal_id, user=request.user)
    meal.delete()
    messages.success(request, 'Meal deleted.')
    
    return redirect(f"{reverse('nutrition_page')}?date={date_param}" if date_param else reverse('nutrition_page'))


@login_required
@require_POST
def add_supplement_to_meal(request):
    meal_id = request.POST.get('meal_id')
    supplement_name = request.POST.get('supplement_name', '').strip()
    supplement_type = request.POST.get('supplement_type', 'other')
    dosage = request.POST.get('dosage', '1')
    unit = request.POST.get('unit', 'serving')
    supplement_id = request.POST.get('supplement_id')
    meal_supplement_id = request.POST.get('meal_supplement_id')  # For editing
    date_param = request.POST.get('date')
    
    if not meal_id or not supplement_name:
        messages.error(request, 'Meal and supplement name are required.')
        return redirect(f"{reverse('nutrition_page')}?date={date_param}" if date_param else reverse('nutrition_page'))
    
    meal = get_object_or_404(Meal, id=meal_id, user=request.user)
    
    supplement_obj = None
    if supplement_id:
        try:
            supplement_obj = SupplementDatabase.objects.get(id=supplement_id)
        except SupplementDatabase.DoesNotExist:
            pass
    
    # Check if this is an update or create
    if meal_supplement_id:
        try:
            meal_supplement = MealSupplement.objects.get(id=meal_supplement_id, meal__user=request.user)
            meal_supplement.name = supplement_name
            meal_supplement.supplement_type = supplement_type
            meal_supplement.dosage = dosage
            meal_supplement.unit = unit
            meal_supplement.supplement = supplement_obj
            meal_supplement.save()
            messages.success(request, f'Supplement "{supplement_name}" updated.')
        except MealSupplement.DoesNotExist:
            messages.error(request, 'Supplement not found.')
    else:
        MealSupplement.objects.create(
            meal=meal,
            supplement=supplement_obj,
            name=supplement_name,
            supplement_type=supplement_type,
            dosage=dosage,
            unit=unit
        )
        messages.success(request, f'Supplement "{supplement_name}" added to {meal.name}.')
    
    return redirect(f"{reverse('nutrition_page')}?date={date_param}")


@login_required
@require_POST
def toggle_meal_supplement(request):
    supplement_id = request.POST.get('supplement_id')
    date_param = request.POST.get('date')
    
    supplement = get_object_or_404(MealSupplement, id=supplement_id, meal__user=request.user)
    supplement.taken = not supplement.taken
    supplement.save()
    
    return redirect(f"{reverse('nutrition_page')}?date={date_param}" if date_param else reverse('nutrition_page'))


@login_required
@require_POST
def delete_meal_supplement(request):
    supplement_id = request.POST.get('supplement_id')
    date_param = request.POST.get('date')
    
    supplement = get_object_or_404(MealSupplement, id=supplement_id, meal__user=request.user)
    supplement.delete()
    messages.success(request, 'Supplement deleted.')
    
    return redirect(f"{reverse('nutrition_page')}?date={date_param}" if date_param else reverse('nutrition_page'))


@login_required
def social_page(request):
    return render(request, 'socal_dir/social_page.html', {'active_tab': 'social'})


@login_required
def search_foods(request):
    """Search existing FoodItems by name and return unique results with nutritional data."""
    query = request.GET.get('q', '').strip()
    if not query or len(query) < 2:
        return JsonResponse({'results': []})
    
    # Search for food items matching the query (case-insensitive)
    food_items = (
        FoodItem.objects
        .filter(name__icontains=query)
        .values('id', 'name', 'calories', 'protein', 'carbs', 'fats')
        .order_by('name')[:20]
    )
    
    # Deduplicate by name (keep entry with best macro data)
    seen_names = {}
    for item in food_items:
        name_lower = item['name'].lower()
        if name_lower not in seen_names:
            seen_names[name_lower] = item
        else:
            existing = seen_names[name_lower]
            existing_score = (existing['protein'] or 0) + (existing['carbs'] or 0) + (existing['fats'] or 0)
            new_score = (item['protein'] or 0) + (item['carbs'] or 0) + (item['fats'] or 0)
            if new_score > existing_score:
                seen_names[name_lower] = item
    
    results = list(seen_names.values())
    return JsonResponse({'results': results})


@login_required
def get_all_foods(request):
    """Get all unique foods from the database for display in the Food Database card."""
    # Get all food items, deduplicated by name
    food_items = (
        FoodItem.objects
        .values('id', 'name', 'calories', 'protein', 'carbs', 'fats')
        .order_by('name')
    )
    
    # Deduplicate by name (keep entry with best macro data)
    seen_names = {}
    for item in food_items:
        name_lower = item['name'].lower()
        if name_lower not in seen_names:
            seen_names[name_lower] = item
        else:
            existing = seen_names[name_lower]
            existing_score = (existing['protein'] or 0) + (existing['carbs'] or 0) + (existing['fats'] or 0)
            new_score = (item['protein'] or 0) + (item['carbs'] or 0) + (item['fats'] or 0)
            if new_score > existing_score:
                seen_names[name_lower] = item
    
    # Sort by name alphabetically
    results = sorted(seen_names.values(), key=lambda x: x['name'].lower())
    return JsonResponse({'foods': results, 'count': len(results)})


@login_required
@require_POST
def save_food_to_database(request):
    """Save a new food or update existing food in the nutrition database."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    food_id = data.get('id')
    name = data.get('name', '').strip()
    calories = data.get('calories', 0)
    protein = data.get('protein', 0)
    carbs = data.get('carbs', 0)
    fats = data.get('fats', 0)
    
    if not name:
        return JsonResponse({'error': 'Food name is required'}, status=400)
    
    try:
        calories = int(calories) if calories else 0
        protein = int(protein) if protein else 0
        carbs = int(carbs) if carbs else 0
        fats = int(fats) if fats else 0
    except ValueError:
        return JsonResponse({'error': 'Invalid numeric values'}, status=400)
    
    # Get or create a system meal for storing database foods
    from django.contrib.auth.models import User
    system_user, _ = User.objects.get_or_create(
        username='system@spotter.ai',
        defaults={'email': 'system@spotter.ai', 'is_active': False}
    )
    system_meal, _ = Meal.objects.get_or_create(
        user=system_user,
        name='Food Database',
        date=date(2000, 1, 1)
    )
    
    if food_id:
        # Update existing food
        try:
            food_item = FoodItem.objects.get(id=food_id)
            food_item.name = name
            food_item.calories = calories
            food_item.protein = protein
            food_item.carbs = carbs
            food_item.fats = fats
            food_item.save()
            return JsonResponse({
                'success': True,
                'message': f'Updated "{name}" in database',
                'food': {
                    'id': food_item.id,
                    'name': food_item.name,
                    'calories': food_item.calories,
                    'protein': food_item.protein,
                    'carbs': food_item.carbs,
                    'fats': food_item.fats,
                }
            })
        except FoodItem.DoesNotExist:
            pass  # Fall through to create new
    
    # Create new food item in database
    food_item = FoodItem.objects.create(
        meal=system_meal,
        name=name,
        calories=calories,
        protein=protein,
        carbs=carbs,
        fats=fats,
        completed=False
    )
    
    return JsonResponse({
        'success': True,
        'message': f'Added "{name}" to database',
        'food': {
            'id': food_item.id,
            'name': food_item.name,
            'calories': food_item.calories,
            'protein': food_item.protein,
            'carbs': food_item.carbs,
            'fats': food_item.fats,
        }
    })


@csrf_exempt
@require_http_methods(["GET"])
def get_all_supplements(request):
    """Get all supplements from the SupplementDatabase for display."""
    supplements = (
        SupplementDatabase.objects
        .all()
        .values('id', 'name', 'supplement_type', 'dosage', 'unit')
        .order_by('name')
    )
    
    return JsonResponse({'supplements': list(supplements)})


@login_required
@csrf_exempt
@require_http_methods(["GET"])
def search_supplements(request):
    """Search SupplementDatabase by name and return results."""
    query = request.GET.get('q', '').strip()
    if not query or len(query) < 2:
        return JsonResponse({'results': []})
    
    supplements = (
        SupplementDatabase.objects
        .filter(name__icontains=query)
        .values('id', 'name', 'supplement_type', 'dosage', 'unit')
        .order_by('name')[:20]
    )
    
    results = list(supplements)
    return JsonResponse({'results': results})


@login_required
@csrf_exempt
@require_http_methods(["POST", "GET"])
def supplement_entries(request):
    """Get or create supplement entries for the logged-in user."""
    if request.method == 'GET':
        date_str = request.GET.get('date')
        if date_str:
            try:
                entry_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                entry_date = date.today()
        else:
            entry_date = date.today()
        
        entries = SupplementEntry.objects.filter(
            user=request.user,
            date=entry_date
        ).values('id', 'name', 'supplement_type', 'dosage', 'unit', 'taken')
        
        return JsonResponse({'entries': list(entries)})
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
        
        name = data.get('name', '').strip()
        supplement_type = data.get('supplement_type', 'other')
        dosage = data.get('dosage', '1')
        unit = data.get('unit', 'serving')
        entry_date = data.get('date', str(date.today()))
        supplement_id = data.get('supplement_id')
        
        if not name:
            return JsonResponse({'success': False, 'error': 'Name is required'}, status=400)
        
        try:
            entry_date = datetime.strptime(entry_date, '%Y-%m-%d').date()
        except ValueError:
            entry_date = date.today()
        
        supplement_obj = None
        if supplement_id:
            try:
                supplement_obj = SupplementDatabase.objects.get(id=supplement_id)
            except SupplementDatabase.DoesNotExist:
                pass
        
        entry = SupplementEntry.objects.create(
            user=request.user,
            supplement=supplement_obj,
            name=name,
            supplement_type=supplement_type,
            dosage=dosage,
            unit=unit,
            date=entry_date,
            taken=False
        )
        
        return JsonResponse({
            'success': True,
            'entry': {
                'id': entry.id,
                'name': entry.name,
                'supplement_type': entry.supplement_type,
                'dosage': entry.dosage,
                'unit': entry.unit,
                'taken': entry.taken,
            }
        })


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def complete_workout(request):
    """Mark a workout as completed."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    
    workout_id = data.get('workout_id')
    
    if not workout_id:
        return JsonResponse({'success': False, 'error': 'workout_id is required'}, status=400)
    
    try:
        workout = Workout.objects.get(id=workout_id, user=request.user)
    except Workout.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Workout not found'}, status=404)
    
    workout.status = 'completed'
    workout.save()
    
    return JsonResponse({
        'success': True,
        'workout_id': workout.id,
        'status': workout.status,
    })


@login_required
@csrf_exempt
@require_http_methods(["PATCH"])
def toggle_supplement_taken(request, entry_id):
    """Toggle the 'taken' status of a supplement entry."""
    try:
        entry = SupplementEntry.objects.get(id=entry_id, user=request.user)
    except SupplementEntry.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Entry not found'}, status=404)
    
    try:
        data = json.loads(request.body)
        taken = data.get('taken', not entry.taken)
    except json.JSONDecodeError:
        taken = not entry.taken
    
    entry.taken = taken
    entry.save()
    
    return JsonResponse({
        'success': True,
        'taken': entry.taken,
    })


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def save_workout_time(request):
    """Save the total duration for a workout."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    
    workout_id = data.get('workout_id')
    total_seconds = data.get('total_seconds')
    
    if not workout_id or total_seconds is None:
        return JsonResponse({'success': False, 'error': 'workout_id and total_seconds are required'}, status=400)
    
    try:
        total_seconds = int(total_seconds)
    except (TypeError, ValueError):
        return JsonResponse({'success': False, 'error': 'total_seconds must be an integer'}, status=400)
    
    try:
        workout = Workout.objects.get(id=workout_id, user=request.user)
    except Workout.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Workout not found'}, status=404)
    
    workout.total_duration_seconds = total_seconds
    workout.save()
    
    return JsonResponse({
        'success': True,
        'workout_id': workout.id,
        'total_seconds': workout.total_duration_seconds,
    })


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def complete_exercises_by_ids(request):
    """Mark specific exercises as completed."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    
    exercise_ids = data.get('exercise_ids', [])
    
    if not exercise_ids or not isinstance(exercise_ids, list):
        return JsonResponse({'success': False, 'error': 'exercise_ids must be a non-empty list'}, status=400)
    
    try:
        exercises = Exercise.objects.filter(id__in=exercise_ids, workout__user=request.user)
        completed_count = 0
        for exercise in exercises:
            if not exercise.completed:
                exercise.completed = True
                exercise.save()
                completed_count += 1
        
        return JsonResponse({
            'success': True,
            'completed_count': completed_count,
            'exercise_ids': list(exercises.values_list('id', flat=True)),
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def save_set_progress(request):
    """Save individual set completion status."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    
    set_data = data.get('set_data', [])  # List of {exercise_id, set_number, completed}
    timer_seconds = data.get('timer_seconds', 0)
    workout_id = data.get('workout_id')
    
    if not set_data or not isinstance(set_data, list):
        return JsonResponse({'success': False, 'error': 'set_data must be a non-empty list'}, status=400)
    
    try:
        from django.db.models import Q
        
        saved_count = 0
        for item in set_data:
            exercise_id = item.get('exercise_id')
            set_number = item.get('set_number')
            completed = item.get('completed', False)
            
            if not exercise_id or not set_number:
                continue
            
            # Verify user owns this exercise
            exercise = Exercise.objects.filter(
                id=exercise_id, 
                workout__user=request.user
            ).first()
            
            if not exercise:
                continue
            
            # Create or update set progress
            from core.models import SetProgress
            progress, created = SetProgress.objects.update_or_create(
                exercise_id=exercise_id,
                set_number=set_number,
                defaults={'completed': completed}
            )
            saved_count += 1
        
        # Save timer seconds to workout if provided
        if workout_id and timer_seconds >= 0:
            workout = Workout.objects.filter(
                id=workout_id,
                user=request.user
            ).first()
            if workout:
                workout.current_session_seconds = timer_seconds
                workout.save(update_fields=['current_session_seconds'])
        
        return JsonResponse({
            'success': True,
            'saved_count': saved_count,
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@csrf_exempt
@require_http_methods(["GET"])
def get_set_progress(request):
    """Get set completion status for a workout's exercises."""
    workout_id = request.GET.get('workout_id')
    
    if not workout_id:
        return JsonResponse({'success': False, 'error': 'workout_id required'}, status=400)
    
    try:
        from core.models import SetProgress
        
        # Verify user owns this workout
        workout = Workout.objects.filter(
            id=workout_id,
            user=request.user
        ).first()
        
        if not workout:
            return JsonResponse({'success': False, 'error': 'Workout not found'}, status=404)
        
        # Get all set progress for this workout's exercises
        progress = SetProgress.objects.filter(
            exercise__workout=workout
        ).values('exercise_id', 'set_number', 'completed')
        
        set_progress_dict = {}
        for item in progress:
            exercise_id = item['exercise_id']
            if exercise_id not in set_progress_dict:
                set_progress_dict[exercise_id] = []
            set_progress_dict[exercise_id].append({
                'set_number': item['set_number'],
                'completed': item['completed']
            })
        
        return JsonResponse({
            'success': True,
            'set_progress': set_progress_dict,
            'timer_seconds': workout.current_session_seconds,
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
