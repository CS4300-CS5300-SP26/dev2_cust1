import logging
import smtplib

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.db import transaction

from .forms import RegistrationForm


def splash(request):
    if request.user.is_authenticated:
        return redirect('home_dash')
    return render(request, 'core/splash.html')


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
                    # TEMPORARILY DISABLED: Email verification
                    # verification = EmailVerification.objects.create(user=user)
                    # verify_url = request.build_absolute_uri(f'/verify_email/{verification.token}/')
                    # html_message = f"""
                    # <div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;padding:32px;background:#111;border-radius:16px;">
                    #     <h1 style="color:#F67D26;text-align:center;">Spotter.ai</h1>
                    #     <p style="color:#fff;font-size:1.1rem;text-align:center;">Welcome! Click the button below to verify your email and activate your account.</p>
                    #     <div style="text-align:center;margin:32px 0;">
                    #         <a href="{verify_url}" style="display:inline-block;padding:16px 48px;background:#F67D26;color:#fff;font-size:1.1rem;font-weight:600;border-radius:12px;text-decoration:none;">Verify My Email</a>
                    #     </div>
                    #     <p style="color:rgba(255,255,255,0.5);font-size:0.85rem;text-align:center;">This link expires in 24 hours. If you didn't create an account, you can ignore this email.</p>
                    # </div>
                    # """
                    # send_mail(
                    #     'Verify your Spotter.ai account',
                    #     f'Click this link to verify your account: {verify_url}',
                    #     settings.DEFAULT_FROM_EMAIL,
                    #     [user.email],
                    #     html_message=html_message,
                    #     fail_silently=False,
                    # )
            except (smtplib.SMTPException, OSError):
                logger.exception('Failed to send verification email during signup for %s', form.cleaned_data['email'])
                form.add_error(None, 'We could not send your verification email right now. Please try again in a moment.')
                return render(request, 'core/user_get_started.html', {'form': form})

            messages.success(request, 'Account created successfully! You can now log in.')
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
    return render(request, 'nutrition_dir/nutrition_page.html', {'active_tab': 'nutrition'})


@login_required
def ai_page(request):
    return render(request, 'ai_dir/ai_page.html', {'active_tab': 'ai'})


@login_required
def social_page(request):
    return render(request, 'socal_dir/social_page.html', {'active_tab': 'social'})
