from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path('', views.splash, name='splash'),
    path('api/chat', views.api_chat, name='api_chat'),
    path('user_get_started/', views.user_get_started, name='user_get_started'),
    path('user_login/', views.user_login, name='user_login'),
    path('user_logout/', views.user_logout, name='user_logout'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    path('reset_password/<uuid:token>/', views.reset_password, name='reset_password'),
    path('home_dash/', views.home_dash, name='home_dash'),
    path('train/', views.train_page, name='train_page'),
    path('train/add_workout/', views.add_workout, name='add_workout'),
    path('train/delete_workout/', views.delete_workout, name='delete_workout'),
    path('train/add_exercise/', views.add_exercise, name='add_exercise'),
    path('train/edit_exercise/', views.edit_exercise, name='edit_exercise'),
    path('train/toggle_exercise/', views.toggle_exercise, name='toggle_exercise'),
    path('train/delete_exercise/', views.delete_exercise, name='delete_exercise'),
    path('nutrition/', views.nutrition_page, name='nutrition_page'),
    path('nutrition/add_meal/', views.add_meal, name='add_meal'),
    path('nutrition/add_food_item/', views.add_food_item, name='add_food_item'),
    path('nutrition/toggle_food_item/', views.toggle_food_item, name='toggle_food_item'),
    path('nutrition/delete_food_item/', views.delete_food_item, name='delete_food_item'),
    path('ai/', views.chat_page, name='ai_page'),
    path('social/', views.social_page, name='social_page'),
    path('verify_email/<uuid:token>/', views.verify_email, name='verify_email'),
    # Social login shortcuts
    path('login/google/', RedirectView.as_view(url='/accounts/google/login/', query_string=True), name='google_login'),
    path('login/apple/', RedirectView.as_view(url='/accounts/apple/login/', query_string=True), name='apple_login'),
    path('login/facebook/', RedirectView.as_view(url='/accounts/facebook/login/', query_string=True), name='facebook_login'),
    path('login/instagram/', RedirectView.as_view(url='/accounts/instagram/login/', query_string=True), name='instagram_login'),
]
