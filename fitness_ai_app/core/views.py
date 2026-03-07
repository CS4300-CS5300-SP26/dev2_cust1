from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .forms import RegistrationForm


def splash(request):
    if request.user.is_authenticated:
        return redirect('home_dash')
    return render(request, 'core/splash.html')


def user_get_started(request):
    if request.user.is_authenticated:
        return redirect('home_dash')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully! Welcome to Spotter.ai.')
            return redirect('home_dash')
        else:
            return render(request, 'core/user_get_started.html', {'form': form})

    form = RegistrationForm()
    return render(request, 'core/user_get_started.html', {'form': form})


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
