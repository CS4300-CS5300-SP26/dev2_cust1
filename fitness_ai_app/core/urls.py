from django.urls import path
from . import views

urlpatterns = [
    path('', views.splash, name='splash'),
    path('user_get_started/', views.user_get_started, name='user_get_started'),
    path('user_login/', views.user_login, name='user_login'),
    path('user_logout/', views.user_logout, name='user_logout'),
    path('home_dash/', views.home_dash, name='home_dash'),
]
