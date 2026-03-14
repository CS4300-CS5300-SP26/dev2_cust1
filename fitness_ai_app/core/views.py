from django.shortcuts import render


def splash(request):
    return render(request, 'core/splash.html')


def nutrition(request):
    return render(request, 'core/nutrition.html')
