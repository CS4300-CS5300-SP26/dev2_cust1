from django.shortcuts import render


def splash(request):
    return render(request, 'core/splash.html')

def user_get_started(request):
    return render(request, 'core/user_get_started.html')

def user_login(request):
    return render(request, 'core/user_login.html')
