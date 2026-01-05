from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Engagement, ControlRequirement, Request


@admin.register(Engagement)
class EngagementAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'lead_auditor', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'lead_auditor__username']
    raw_id_fields = ['lead_auditor']


@admin.register(ControlRequirement)
class ControlRequirementAdmin(admin.ModelAdmin):
    list_display = ['control_id', 'engagement', 'created_at']
    list_filter = ['engagement', 'created_at']
    search_fields = ['control_id', 'description', 'engagement__title']
    raw_id_fields = ['engagement']


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ['linked_control', 'assignee', 'status', 'is_locked', 'reviewed_by', 'reviewed_at']
    list_filter = ['status', 'is_locked', 'created_at']
    search_fields = ['linked_control__control_id', 'assignee__username', 'auditor_test_notes']
    raw_id_fields = ['linked_control', 'assignee', 'prepared_by', 'reviewed_by']
    readonly_fields = ['is_locked', 'reviewed_at', 'created_at', 'updated_at']
    actions = ['unlock_request']
    
    fieldsets = (
        ('Request Information', {
            'fields': ('linked_control', 'assignee', 'status')
        }),
        ('Files', {
            'fields': ('evidence_file', 'workpaper_file')
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
        queryset.update(is_locked=False, status='In-Review')
        self.message_user(request, f"{queryset.count()} request(s) unlocked.")
    unlock_request.short_description = "Unlock selected requests"
