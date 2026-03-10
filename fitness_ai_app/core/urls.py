from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path('', views.splash, name='splash'),
    path('user_get_started/', views.user_get_started, name='user_get_started'),
    path('user_login/', views.user_login, name='user_login'),
    path('user_logout/', views.user_logout, name='user_logout'),
    path('home_dash/', views.home_dash, name='home_dash'),
    path('verify_email/<uuid:token>/', views.verify_email, name='verify_email'),
    # Social login shortcuts
    path('login/google/', RedirectView.as_view(url='/accounts/google/login/', query_string=True), name='google_login'),
    path('login/apple/', RedirectView.as_view(url='/accounts/apple/login/', query_string=True), name='apple_login'),
    path('login/facebook/', RedirectView.as_view(url='/accounts/facebook/login/', query_string=True), name='facebook_login'),
    path('login/instagram/', RedirectView.as_view(url='/accounts/instagram/login/', query_string=True), name='instagram_login'),
]
