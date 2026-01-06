from django import forms
from .models import Engagement, ControlRequirement, Request


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


class ControlRequirementForm(forms.ModelForm):
    year = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_year'}),
        choices=[('', 'Select Year')]
    )
    
    class Meta:
        model = ControlRequirement
        fields = ['engagement', 'year', 'control_id', 'description', 'testing_procedure']
        widgets = {
            'engagement': forms.Select(attrs={'class': 'form-select', 'id': 'id_engagement'}),
            'control_id': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'testing_procedure': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Generate year choices dynamically (1985 to 2050)
        year_choices = [('', 'Select Year')] + [(str(year), year) for year in range(1985, 2051)]
        self.fields['year'].choices = year_choices
    
    def clean(self):
        cleaned_data = super().clean()
        engagement = cleaned_data.get('engagement')
        year = cleaned_data.get('year')
        
        if engagement and not year:
            raise forms.ValidationError({
                'year': 'Year is required when an engagement is selected.'
            })
        
        if year:
            try:
                year_int = int(year)
                if year_int < 1985 or year_int > 2050:
                    raise forms.ValidationError({
                        'year': 'Year must be between 1985 and 2050.'
                    })
                # Convert to integer for saving
                cleaned_data['year'] = year_int
            except (ValueError, TypeError):
                raise forms.ValidationError({
                    'year': 'Please select a valid year.'
                })
        
        return cleaned_data


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
