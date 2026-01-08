from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Engagement, EngagementControl, Request, Standard, StandardControl, Questionnaire, QuestionnaireQuestion, QuestionnaireResponse


@admin.register(Engagement)
class EngagementAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'lead_auditor', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'lead_auditor__username']
    raw_id_fields = ['lead_auditor']


@admin.register(EngagementControl)
class EngagementControlAdmin(admin.ModelAdmin):
    list_display = ['control_id', 'control_name', 'engagement', 'source', 'created_at']
    list_filter = ['engagement', 'source', 'created_at']
    search_fields = ['control_id', 'control_name', 'control_description', 'engagement__title']
    raw_id_fields = ['engagement', 'standard_control']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Standard)
class StandardAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name', 'description']


@admin.register(StandardControl)
class StandardControlAdmin(admin.ModelAdmin):
    list_display = ['control_id', 'standard', 'is_active']
    list_filter = ['standard', 'is_active']
    search_fields = ['control_id', 'control_description']
    raw_id_fields = ['standard']


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ['linked_control', 'assignee', 'status', 'is_locked', 'preparer_signed', 'reviewer_signed', 'reviewed_by', 'reviewed_at']
    list_filter = ['status', 'is_locked', 'preparer_signed', 'reviewer_signed', 'created_at']
    search_fields = ['linked_control__control_id', 'assignee__username', 'auditor_test_notes']
    raw_id_fields = ['linked_control', 'assignee', 'prepared_by', 'reviewed_by']
    readonly_fields = ['is_locked', 'created_at', 'updated_at']
    actions = ['unlock_request']
    
    fieldsets = (
        ('Request Information', {
            'fields': ('linked_control', 'assignee', 'status')
        }),
        ('Request Details', {
            'fields': ('title', 'description', 'due_date', 'tags')
        }),
        ('Sign-off', {
            'fields': ('auditor_test_notes', 'prepared_by', 'reviewed_by', 'reviewed_at', 'is_locked')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def unlock_request(self, request, queryset):
        # Unlock and recalculate status for each request
        for req in queryset:
            req.is_locked = False
            req.recalculate_status()
            req.save()
        self.message_user(request, f"{queryset.count()} request(s) unlocked.")
    unlock_request.short_description = "Unlock selected requests"


@admin.register(Questionnaire)
class QuestionnaireAdmin(admin.ModelAdmin):
    list_display = ['name', 'engagement', 'standard', 'status', 'respondent', 'updated_at']
    list_filter = ['status', 'standard', 'created_at']
    search_fields = ['name', 'engagement__title', 'standard__name']
    raw_id_fields = ['engagement', 'standard', 'respondent']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(QuestionnaireQuestion)
class QuestionnaireQuestionAdmin(admin.ModelAdmin):
    list_display = ['questionnaire', 'control', 'order']
    list_filter = ['questionnaire', 'control__standard']
    search_fields = ['question_text', 'control__control_id']
    raw_id_fields = ['questionnaire', 'control']


@admin.register(QuestionnaireResponse)
class QuestionnaireResponseAdmin(admin.ModelAdmin):
    list_display = ['questionnaire', 'question', 'answer', 'answered_by', 'answered_at']
    list_filter = ['answer', 'answered_at']
    search_fields = ['questionnaire__name', 'question__control__control_id']
    raw_id_fields = ['questionnaire', 'question', 'answered_by']
    readonly_fields = ['answered_at']
