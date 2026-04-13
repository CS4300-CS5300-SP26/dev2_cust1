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
from .models import Meal, FoodItem, Workout, Exercise, PasswordReset, SupplementDatabase, SupplementEntry, MealSupplement


def splash(request):
    if request.user.is_authenticated:
        return redirect('home_dash')
    return render(request, 'core/splash.html')


@login_required
def chat_page(request):
    return render(request, 'core/chat.html')


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
    return redirect('home_dash')


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
    return render(request, 'home_dash_dir/home_dash.html', {'active_tab': 'home'})


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

    workouts = (
        Workout.objects.filter(user=request.user, date=selected_date)
        .prefetch_related('exercises')
    )

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
        'is_past_date': is_past_date,
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
    sets = request.POST.get('sets', '').strip()
    reps = request.POST.get('reps', '').strip()
    weight = request.POST.get('weight', '').strip()
    status = request.POST.get('status', 'planned').strip()
    date_param = request.POST.get('date')

    if not workout_id or not exercise_name or not muscle_group:
        messages.error(request, 'Exercise name and muscle group are required.')
        return redirect(f"{reverse('train_page')}?date={date_param}" if date_param else reverse('train_page'))

    workout = get_object_or_404(Workout, id=workout_id, user=request.user)

    Exercise.objects.create(
        workout=workout,
        name=exercise_name,
        muscle_group=muscle_group,
        sets=int(sets) if sets else None,
        reps=int(reps) if reps else None,
        weight=int(weight) if weight else None,
        completed=(status == 'completed'),
    )
    return redirect(f"{reverse('train_page')}?date={date_param}")


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
    exercise.name = exercise_name
    exercise.muscle_group = muscle_group
    exercise.sets = int(sets) if sets else None
    exercise.reps = int(reps) if reps else None
    exercise.weight = int(weight) if weight else None
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

    calorie_goal = 2400
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
def add_supplement_to_meal(request):
    meal_id = request.POST.get('meal_id')
    supplement_name = request.POST.get('supplement_name', '').strip()
    supplement_type = request.POST.get('supplement_type', 'other')
    dosage = request.POST.get('dosage', '1')
    unit = request.POST.get('unit', 'serving')
    supplement_id = request.POST.get('supplement_id')
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
