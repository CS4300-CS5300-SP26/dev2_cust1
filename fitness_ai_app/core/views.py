from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .forms import RegistrationForm


def splash(request):
    if request.user.is_authenticated:
        return redirect('home_dash')
    return render(request, 'core/splash.html')


from django.core.mail import send_mail
import random
from .models import EmailVerification

def user_get_started(request):
    if request.user.is_authenticated:
        return redirect('home_dash')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Generate 6-digit code
            code = f"{random.randint(100000, 999999)}"
            EmailVerification.objects.create(user=user, code=code)
            send_mail(
                'Spotter.ai Email Verification',
                f'Your verification code is: {code}',
                'spotter.ai2026@gmail.com',
                [user.email],
                fail_silently=False,
            )
            messages.info(request, 'A verification code has been sent to your email. Please enter it below to activate your account.')
            return redirect('verify_code', user_id=user.id)
        else:
            return render(request, 'core/user_get_started.html', {'form': form})

    form = RegistrationForm()
    return render(request, 'core/user_get_started.html', {'form': form})


def verify_code(request, user_id):
    from .models import EmailVerification
    from django.contrib.auth.models import User
    try:
        user = User.objects.get(id=user_id)
        verification = EmailVerification.objects.get(user=user)
    except (User.DoesNotExist, EmailVerification.DoesNotExist):
        messages.error(request, 'Invalid verification link.')
        return redirect('user_get_started')

    if request.method == 'POST':
        code_entered = request.POST.get('code', '').strip()
        if verification.code == code_entered and not verification.is_expired():
            verification.verified = True
            verification.save()
            user.is_active = True
            user.save()
            messages.success(request, 'Your account has been activated! You can now log in.')
            return redirect('user_login')
        elif verification.is_expired():
            messages.error(request, 'Verification code expired. Please sign up again.')
            user.delete()
            return redirect('user_get_started')
        else:
            messages.error(request, 'Invalid code. Please try again.')
    return render(request, 'core/verify_code.html', {'user_id': user_id})


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
    return render(request, 'home_dash_dir/home_dash.html')
