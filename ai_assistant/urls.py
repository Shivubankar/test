from django.urls import path
from . import views


urlpatterns = [
    path('', views.ai_assistant_home, name='ai_assistant_home'),
    path('upload/', views.upload_document, name='ai_assistant_upload'),
    path('chat/', views.send_message, name='ai_assistant_chat'),
]
