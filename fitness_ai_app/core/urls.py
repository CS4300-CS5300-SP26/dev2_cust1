from django.urls import path
from . import views

urlpatterns = [
    path('', views.splash, name='splash'),
    path('api/chat', views.api_chat, name='api_chat'),
    path('chat/', views.chat_page, name='chat_page'),
]
