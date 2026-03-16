from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from datetime import datetime, date, timedelta

from .forms import RegistrationForm
from .models import Meal, FoodItem


def splash(request):
    if request.user.is_authenticated:
        return redirect('home_dash')
    return render(request, 'core/splash.html')


from django.core.mail import send_mail
from .models import EmailVerification

def user_get_started(request):
    if request.user.is_authenticated:
        return redirect('home_dash')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            verification = EmailVerification.objects.create(user=user)
            verify_url = request.build_absolute_uri(f'/verify_email/{verification.token}/')
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
            send_mail(
                'Verify your Spotter.ai account',
                f'Click this link to verify your account: {verify_url}',
                'spotter.ai2026@gmail.com',
                [user.email],
                html_message=html_message,
                fail_silently=False,
            )
            messages.success(request, 'A verification link has been sent to your email. Please check your inbox and click the link to activate your account.')
            return redirect('user_login')
        else:
            return render(request, 'core/user_get_started.html', {'form': form})

    form = RegistrationForm()
    return render(request, 'core/user_get_started.html', {'form': form})


def verify_email(request, token):
    from django.contrib.auth.models import User
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


def user_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('splash')


@login_required
def home_dash(request):
    return render(request, 'home_dash_dir/home_dash.html', {'active_tab': 'home'})


@login_required
def train_page(request):
    return render(request, 'train_dir/train_page.html', {'active_tab': 'train'})


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
    
    meals = Meal.objects.filter(user=request.user, date=selected_date).prefetch_related('items')
    
    prev_date = (selected_date - timedelta(days=1)).strftime('%Y-%m-%d')
    next_date = (selected_date + timedelta(days=1)).strftime('%Y-%m-%d')
    
    context = {
        'active_tab': 'nutrition',
        'meals': meals,
        'selected_date': selected_date,
        'date_string': selected_date.strftime('%Y-%m-%d'),
        'prev_date': prev_date,
        'next_date': next_date,
    }
    return render(request, 'nutrition_dir/nutrition_page.html', context)


@login_required
@require_POST
def add_meal(request):
    meal_name = request.POST.get('meal_name', '').strip()
    date_param = request.POST.get('date')
    
    if not meal_name or not date_param:
        messages.error(request, 'Meal name and date are required.')
        return redirect(f'/nutrition/?date={date_param}' if date_param else '/nutrition/')
    
    try:
        meal_date = datetime.strptime(date_param, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, 'Invalid date format.')
        return redirect('/nutrition/')
    
    Meal.objects.create(user=request.user, name=meal_name, date=meal_date)
    messages.success(request, f'Meal "{meal_name}" added successfully.')
    return redirect(f'/nutrition/?date={date_param}')


@login_required
@require_POST
def add_food_item(request):
    meal_id = request.POST.get('meal_id')
    food_name = request.POST.get('food_name', '').strip()
    food_calories = request.POST.get('food_calories', '0')
    date_param = request.POST.get('date')
    
    if not meal_id or not food_name or not food_calories:
        messages.error(request, 'All fields are required.')
        return redirect(f'/nutrition/?date={date_param}' if date_param else '/nutrition/')
    
    meal = get_object_or_404(Meal, id=meal_id, user=request.user)
    
    try:
        calories = int(food_calories)
    except ValueError:
        messages.error(request, 'Calories must be a number.')
        return redirect(f'/nutrition/?date={date_param}')
    
    FoodItem.objects.create(meal=meal, name=food_name, calories=calories)
    messages.success(request, f'Food item "{food_name}" added to {meal.name}.')
    return redirect(f'/nutrition/?date={date_param}')


@login_required
@require_POST
def toggle_food_item(request):
    item_id = request.POST.get('item_id')
    date_param = request.POST.get('date')
    
    food_item = get_object_or_404(FoodItem, id=item_id, meal__user=request.user)
    food_item.completed = not food_item.completed
    food_item.save()
    
    return redirect(f'/nutrition/?date={date_param}' if date_param else '/nutrition/')


@login_required
@require_POST
def delete_food_item(request):
    item_id = request.POST.get('item_id')
    date_param = request.POST.get('date')
    
    food_item = get_object_or_404(FoodItem, id=item_id, meal__user=request.user)
    food_item.delete()
    messages.success(request, 'Food item deleted.')
    
    return redirect(f'/nutrition/?date={date_param}' if date_param else '/nutrition/')


@login_required
def ai_page(request):
    return render(request, 'ai_dir/ai_page.html', {'active_tab': 'ai'})


@login_required
def social_page(request):
    return render(request, 'socal_dir/social_page.html', {'active_tab': 'social'})
