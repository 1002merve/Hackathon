# Path: member/urls.py

from django.urls import path
from . import views

app_name = 'member'

urlpatterns = [
    # Authentication
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    
    # Multi-step registration
    path('register/step1/', views.register_step1, name='register_step1'),
    path('register/step2/', views.register_step2, name='register_step2'),
    path('register/step3/', views.register_step3, name='register_step3'),
    path('register/step4/', views.register_step4, name='register_step4'),
    
    # AJAX checks
    path('register/check-username/', views.register_check_username, name='check_username'),
    path('register/check-email/', views.register_check_email, name='check_email'),
    
    # Profile
    path('profile/', views.profile_view, name='profile'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Avatar
    path('avatar/create/', views.avatar_create, name='avatar_create'),
    path('avatar/chat/', views.avatar_chat, name='avatar_chat'),
]