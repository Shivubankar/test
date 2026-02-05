from django.urls import path
from . import views

urlpatterns = [
    # Main navigation modules
    path('', views.dashboard, name='dashboard'),
    path('sheets/', views.sheets, name='sheets'),
    path('forms/', views.forms, name='forms'),
    path('questionnaires/', views.questionnaires, name='questionnaires'),
    path('excel-upload/', views.upload_controls_from_excel, name='excel_upload'),
    path('questionnaires/create/<int:engagement_id>/', views.create_questionnaire, name='create_questionnaire'),
    path('questionnaires/<int:questionnaire_id>/', views.questionnaire_detail, name='questionnaire_detail'),
    path('requests/', views.requests_list, name='requests_list'),
    path('requests/<int:pk>/', views.request_detail, name='request_detail'),
    path('create-request/<int:control_id>/', views.create_request, name='create_request'),
    path('documents/', views.documents, name='documents'),
    path('documents/export/', views.export_documents, name='export_documents'),
    path('documents/upload/', views.documents_upload, name='documents_upload'),
    path('generate-sheets/<int:engagement_id>/', views.generate_sheets, name='generate_sheets'),
    
    # Utility endpoints (removed get_years - no year filtering on controls)
    
    # Request actions
    path('upload-evidence/<int:request_id>/', views.upload_evidence, name='upload_evidence'),
    path('upload-evidence-from-sheets/<int:control_id>/', views.upload_evidence_from_sheets, name='upload_evidence_from_sheets'),
    path('upload-workpaper/<int:request_id>/', views.upload_workpaper, name='upload_workpaper'),
    path('merge-request/<int:request_id>/', views.merge_request, name='merge_request'),
    path('undo-merge-request/<int:request_id>/', views.undo_merge_request, name='undo_merge_request'),
    path('signoff-request/<int:request_id>/', views.signoff_request, name='signoff_request'),
    path('undo-signoff-request/<int:request_id>/', views.undo_signoff_request, name='undo_signoff_request'),
    path('unlock-request/<int:request_id>/', views.unlock_request, name='unlock_request'),
    path('delete-doc/<int:doc_id>/', views.delete_document, name='delete_document'),
    
    # File operations (legacy support)
    path('download/<str:file_type>/<int:request_id>/', views.download_file, name='download_file'),
    path('delete/<str:file_type>/<int:request_id>/', views.delete_file, name='delete_file'),
    
    # Creation forms
    path('create-engagement/', views.create_engagement, name='create_engagement'),
    path('create-control/', views.create_control, name='create_control'),
    path('controls/<int:control_id>/signoff/', views.signoff_control, name='signoff_control'),
    path('controls/<int:control_id>/undo-signoff/', views.undo_signoff_control, name='undo_signoff_control'),
    path('sheets/autosave-field/', views.autosave_control_field, name='autosave_control_field'),
    path('update-control/<int:control_id>/', views.update_control, name='update_control'),
    path('upload-workpaper-control/<int:control_id>/', views.upload_workpaper_control, name='upload_workpaper_control'),
    
    # Auth
    path('logout/', views.logout_view, name='logout'),
]
