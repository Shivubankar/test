from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('upload-evidence/<int:request_id>/', views.upload_evidence, name='upload_evidence'),
    path('upload-workpaper/<int:request_id>/', views.upload_workpaper, name='upload_workpaper'),
    path('review-request/<int:request_id>/', views.review_request, name='review_request'),
    path('unlock-request/<int:request_id>/', views.unlock_request, name='unlock_request'),
    path('download/<str:file_type>/<int:request_id>/', views.download_file, name='download_file'),
    path('create-engagement/', views.create_engagement, name='create_engagement'),
    path('create-control/', views.create_control, name='create_control'),
]
