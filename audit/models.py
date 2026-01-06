from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Engagement(models.Model):
    STATUS_CHOICES = [
        ('Planning', 'Planning'),
        ('Fieldwork', 'Fieldwork'),
        ('Archived', 'Archived'),
    ]
    
    title = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Planning')
    lead_auditor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='lead_engagements')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class ControlRequirement(models.Model):
    engagement = models.ForeignKey(Engagement, on_delete=models.CASCADE, related_name='controls')
    year = models.IntegerField(null=True, blank=True, help_text="Year for the control (1985-2050)")
    control_id = models.CharField(max_length=100)
    description = models.TextField()
    testing_procedure = models.TextField(verbose_name="Test Identified")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['control_id']
        unique_together = [['engagement', 'control_id']]
    
    def __str__(self):
        return f"{self.control_id} - {self.engagement.title}"


class Request(models.Model):
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('In-Review', 'In-Review'),
        ('Accepted', 'Accepted'),
        ('Returned', 'Returned'),
    ]
    
    linked_control = models.ForeignKey(ControlRequirement, on_delete=models.CASCADE, related_name='requests')
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_requests')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Open')
    
    # Sign-off fields
    auditor_test_notes = models.TextField(blank=True, verbose_name="Test Performed")
    prepared_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='prepared_requests')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_requests')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Locking
    is_locked = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['linked_control__control_id']
    
    def __str__(self):
        return f"{self.linked_control.control_id} - {self.status}"
    
    def clean(self):
        """
        Business rule for acceptance/sign-off:
        - A request can be accepted if EITHER:
          * At least one supporting file is present (evidence OR workpaper), OR
          * Non-empty 'Test Performed' notes are provided.
        - Whitespace-only notes do not count as valid.
        """
        if self.status == 'Accepted' and not self.is_locked:
            has_file = self.documents.filter(doc_type__in=['evidence', 'workpaper']).exists()
            has_notes = bool(self.auditor_test_notes and self.auditor_test_notes.strip())
            if not (has_file or has_notes):
                raise ValidationError(
                    "Either a supporting file (evidence or workpaper) "
                    "or non-empty 'Test Performed' notes are required before acceptance."
                )
    
    def save(self, *args, **kwargs):
        if self.status == 'Accepted' and not self.is_locked:
            self.is_locked = True
            from django.utils import timezone
            if not self.reviewed_at:
                self.reviewed_at = timezone.now()
        super().save(*args, **kwargs)


class RequestDocument(models.Model):
    DOC_TYPE_CHOICES = [
        ('evidence', 'Evidence'),
        ('workpaper', 'Workpaper'),
    ]

    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to='request_docs/%Y/%m/%d/')
    doc_type = models.CharField(max_length=20, choices=DOC_TYPE_CHOICES)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.doc_type} - {self.file.name}"
