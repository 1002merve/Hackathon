# Path: core/urls.py

from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Chat URLs
    path('chat/', views.chat_view, name='chat'),
    path('chat/stream/', views.chat_stream_response, name='chat_stream'),
    path('chat/sessions/', views.chat_sessions, name='chat_sessions'),
    path('chat/session/<uuid:session_id>/', views.chat_session_detail, name='chat_session_detail'),
    path('chat/session/<uuid:session_id>/load/', views.load_chat_session, name='load_chat_session'),
    path('chat/session/<uuid:session_id>/delete/', views.delete_chat_session, name='delete_chat_session'),
    path('chat/session/<uuid:session_id>/continue/', views.continue_chat_session, name='continue_chat_session'),
    path('chat/history/', views.chat_history, name='chat_history'),
    path('chat/export/', views.export_chat_history, name='export_chat_history'),
    
    # Video URLs - YENİ
    path('chat/video/generate/', views.generate_chat_video, name='generate_chat_video'),
    path('video/<uuid:video_id>/', views.chat_video_detail, name='chat_video_detail'),
    path('video/<uuid:video_id>/status/', views.chat_video_status, name='chat_video_status'),
    path('video/<uuid:video_id>/download/', views.download_chat_video, name='download_chat_video'),
    path('video/<uuid:video_id>/stream/', views.stream_chat_video, name='stream_chat_video'),
    path('video/<uuid:video_id>/delete/', views.delete_chat_video, name='delete_chat_video'),
    path('session/<uuid:session_id>/videos/', views.get_session_videos, name='get_session_videos'),
    
    # Solution URLs
    path('solutions/', views.solutions_list, name='solutions'),
    path('solutions/subject/<int:subject_id>/', views.solutions_list, name='solutions_by_subject'),
    path('solution/<int:solution_id>/', views.solution_detail, name='solution_detail'),
    
    # Settings URLs
    path('settings/', views.settings_view, name='settings'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    
    # API URLs
    path('api/user-stats/', views.get_user_stats, name='user_stats'),
    path('api/chat-sessions/', views.get_chat_sessions_api, name='chat_sessions_api'),
    
    # Topic URLs
    path('topics/', views.topic_tutorial, name='topic_tutorial'),
    path('topic/<int:topic_id>/', views.topic_detail, name='topic_detail'),
    path('education/create/', views.create_education, name='create_education'),
    path('education/<uuid:session_id>/', views.education_session_detail, name='education_session_detail'),
]