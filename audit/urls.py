from django.urls import path
from . import views

urlpatterns = [
    # Main navigation modules
    path('', views.dashboard, name='dashboard'),
    path('sheets/', views.sheets, name='sheets'),
    path('forms/', views.forms, name='forms'),
    path('questionnaires/', views.questionnaires, name='questionnaires'),
    path('questionnaires/create/<int:engagement_id>/', views.create_questionnaire, name='create_questionnaire'),
    path('questionnaires/<int:questionnaire_id>/', views.questionnaire_detail, name='questionnaire_detail'),
    path('requests/', views.requests_list, name='requests_list'),
    path('create-request/<int:control_id>/', views.create_request, name='create_request'),
    path('documents/', views.documents, name='documents'),
    path('documents/upload/', views.documents_upload, name='documents_upload'),
    path('generate-sheets/<int:engagement_id>/', views.generate_sheets, name='generate_sheets'),
    
    # Utility endpoints (removed get_years - no year filtering on controls)
    
    # Request actions
    path('upload-evidence/<int:request_id>/', views.upload_evidence, name='upload_evidence'),
    path('upload-workpaper/<int:request_id>/', views.upload_workpaper, name='upload_workpaper'),
    path('review-request/<int:request_id>/', views.review_request, name='review_request'),
    path('unlock-request/<int:request_id>/', views.unlock_request, name='unlock_request'),
    path('delete-doc/<int:doc_id>/', views.delete_document, name='delete_document'),
    
    # File operations (legacy support)
    path('download/<str:file_type>/<int:request_id>/', views.download_file, name='download_file'),
    path('delete/<str:file_type>/<int:request_id>/', views.delete_file, name='delete_file'),
    
    # Creation forms
    path('create-engagement/', views.create_engagement, name='create_engagement'),
    path('create-control/', views.create_control, name='create_control'),
    path('controls/<int:control_id>/signoff/', views.signoff_control, name='signoff_control'),
    path('update-control/<int:control_id>/', views.update_control, name='update_control'),
    path('upload-workpaper-control/<int:control_id>/', views.upload_workpaper_control, name='upload_workpaper_control'),
    
    # Auth
    path('logout/', views.logout_view, name='logout'),
]
