from django import forms
from .models import Engagement, EngagementControl, Request


class EngagementForm(forms.ModelForm):
    class Meta:
        model = Engagement
        fields = ['title', 'status', 'lead_auditor']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'lead_auditor': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.contrib.auth.models import User
        self.fields['lead_auditor'].queryset = User.objects.all().order_by('username')


# ControlRequirementForm removed - controls are auto-generated from Standards
# Manual control creation is handled directly in views without forms


class EvidenceUploadForm(forms.ModelForm):
    class Meta:
        model = Request
        fields = []
        widgets = {
        }


class WorkpaperUploadForm(forms.ModelForm):
    class Meta:
        model = Request
        fields = ['auditor_test_notes']
        widgets = {
            'auditor_test_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter test performed notes...'}),
        }


class RequestReviewForm(forms.ModelForm):
    class Meta:
        model = Request
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def clean_status(self):
        status = self.cleaned_data.get('status')
        instance = self.instance
        
        if status == 'Accepted':
            # Mirror model-level business rule:
            # Acceptance is allowed if either a supporting file is present
            # (evidence OR workpaper) OR non-empty 'Test Performed' notes exist.
            has_file = bool(instance.workpaper_file or instance.evidence_file)
            has_notes = bool(instance.auditor_test_notes and instance.auditor_test_notes.strip())
            if not (has_file or has_notes):
                raise forms.ValidationError(
                    "Either a supporting file (evidence or workpaper) "
                    "or non-empty 'Test Performed' notes are required before acceptance."
                )
        
        return status
