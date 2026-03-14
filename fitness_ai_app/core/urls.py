from django.urls import path
from . import views

urlpatterns = [
    path('', views.splash, name='splash'),
    path('nutrition/', views.nutrition, name='nutrition'),
]
