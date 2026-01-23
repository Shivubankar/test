from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models.signals import m2m_changed
from django.dispatch import receiver


class Standard(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class StandardControl(models.Model):
    standard = models.ForeignKey(Standard, on_delete=models.CASCADE, related_name='controls')
    control_id = models.CharField(max_length=100, help_text="Control identifier (e.g., A.5.1)")
    title = models.CharField(max_length=500, blank=True, help_text="Control title")
    control_description = models.TextField(help_text="Detailed control description")
    domain = models.CharField(max_length=200, blank=True, help_text="Control domain (e.g., Organizational Controls)")
    standard_reference = models.CharField(max_length=200, blank=True)
    default_testing_type = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = [['standard', 'control_id']]
        ordering = ['standard__name', 'control_id']
    
    def __str__(self):
        return f"{self.standard.name}: {self.control_id}"


class Engagement(models.Model):
    STATUS_CHOICES = [
        ('Planning', 'Planning'),
        ('Fieldwork', 'Fieldwork'),
        ('Archived', 'Archived'),
    ]
    
    title = models.CharField(max_length=200)
    client_name = models.CharField(max_length=200, blank=True)
    audit_year = models.IntegerField(null=True, blank=True, help_text="Year for the audit")
    standards = models.ManyToManyField(Standard, related_name='engagements', help_text="Selected audit standards (e.g., ISO 27001, SOC 2)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Planning')
    lead_auditor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='lead_engagements')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def generate_controls_from_standards(self):
        """
        Auto-generate EngagementControl rows from selected standards.
        Called during engagement creation or when standards are added.
        """
        from .services import generate_engagement_controls
        return generate_engagement_controls(self)


@receiver(m2m_changed, sender=Engagement.standards.through)
def engagement_standards_changed(sender, instance, action, pk_set, **kwargs):
    """
    Auto-generate EngagementControl rows when standards are added to an engagement.
    This ensures rows are created both on engagement creation and when standards are added later.
    """
    if action == 'post_add':
        # Standards were added - generate controls
        instance.generate_controls_from_standards()


class EngagementControl(models.Model):
    """
    Represents a control row in Sheets (Workplan) for a specific engagement.
    These are AUTO-GENERATED from Standards or Questionnaires during engagement creation.
    Sheets represent auditor workpapers, not questionnaire results.
    """
    SOURCE_CHOICES = [
        ('auto', 'Auto-Generated from Standard'),
        ('manual', 'Manual/Custom'),
        ('questionnaire', 'Generated from Questionnaire'),
        ('excel', 'Generated from Excel Upload'),
    ]
    
    engagement = models.ForeignKey(Engagement, on_delete=models.CASCADE, related_name='controls')
    standard_control = models.ForeignKey(StandardControl, on_delete=models.SET_NULL, null=True, blank=True, related_name='engagement_controls', help_text="Source control from Standard Library")
    control_id = models.CharField(max_length=100, help_text="Control ID (e.g., A.5.1)")
    control_name = models.CharField(max_length=200, blank=True, help_text="Control name/title")
    control_description = models.TextField(help_text="Control description")
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='auto')
    
    # Testing fields (auditor workpapers - NOT from questionnaires)
    # These fields are EMPTY by default and ONLY filled by auditors
    test_applied = models.CharField(max_length=200, blank=True, verbose_name="Test Applied", help_text="Auditor-planned test method (empty by default, fully editable)")
    test_performed = models.TextField(blank=True, verbose_name="Test Performed", help_text="Auditor execution notes – free text (empty by default, fully editable)")
    test_results = models.TextField(blank=True, verbose_name="Test Results", help_text="Audit conclusion – free text (e.g., 'No exceptions noted')")
    
    # Sign-offs (independent by role)
    preparer_signed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='controls_prepared')
    preparer_signed_at = models.DateTimeField(null=True, blank=True)
    reviewer_signed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='controls_reviewed')
    reviewer_signed_at = models.DateTimeField(null=True, blank=True)
    admin_signed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='controls_admin_signed')
    admin_signed_at = models.DateTimeField(null=True, blank=True)
    
    # Legacy fields (deprecated - kept for migration compatibility)
    testing_procedure = models.TextField(blank=True, verbose_name="Test Identified", help_text="Deprecated - use test_applied")
    
    # Metadata (updated by Forms)
    metadata = models.JSONField(blank=True, default=dict, help_text="Additional metadata from Forms")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['control_id']
        unique_together = [['engagement', 'control_id']]
        verbose_name = "Engagement Control"
        verbose_name_plural = "Engagement Controls"
    
    def __str__(self):
        return f"{self.control_id} - {self.engagement.title}"
    
    def get_questionnaire_responses(self):
        """
        Get questionnaire responses for this control (read-only reference).
        Returns list of QuestionnaireResponse objects linked to this control via StandardControl.
        """
        from .models import QuestionnaireResponse
        if not self.standard_control:
            return QuestionnaireResponse.objects.none()
        
        # Find questionnaire responses that reference this control
        return QuestionnaireResponse.objects.filter(
            question__control=self.standard_control,
            questionnaire__engagement=self.engagement,
            answer__isnull=False
        ).select_related('questionnaire', 'question', 'answered_by').order_by('-answered_at')


class Request(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('READY_FOR_REVIEW', 'Ready for Review'),
        ('COMPLETED', 'Completed'),
    ]
    
    linked_control = models.ForeignKey(EngagementControl, on_delete=models.CASCADE, related_name='requests')
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    tags = models.CharField(max_length=250, blank=True, help_text="Comma-separated tags")
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_requests')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    
    # Sign-off fields
    auditor_test_notes = models.TextField(blank=True, verbose_name="Test Performed")
    test_results = models.TextField(blank=True, verbose_name="Test Results")
    
    # Preparer sign-off
    preparer_signed = models.BooleanField(default=False)
    prepared_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='prepared_requests')
    preparer_signed_at = models.DateTimeField(null=True, blank=True)
    
    # Reviewer sign-off
    reviewer_signed = models.BooleanField(default=False)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_requests')
    reviewed_at = models.DateTimeField(null=True, blank=True)  # Keep existing field name for compatibility
    
    # Locking (for completed requests - evidence becomes read-only)
    is_locked = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['linked_control__control_id']
    
    def __str__(self):
        return f"{self.linked_control.control_id} - {self.status}"
    
    def recalculate_status(self):
        """
        Automatically recalculate request status based on sign-off boolean flags.
        
        Status mapping:
        - OPEN: preparer_signed = False
        - READY_FOR_REVIEW: preparer_signed = True AND reviewer_signed = False
        - COMPLETED: preparer_signed = True AND reviewer_signed = True
        """
        # Status is derived from sign-off flags only
        if not self.preparer_signed:
            new_status = 'OPEN'
        elif self.preparer_signed and not self.reviewer_signed:
            new_status = 'READY_FOR_REVIEW'
        else:
            new_status = 'COMPLETED'
        
        # Update status and lock state
        self.status = new_status
        # Auto-lock when completed
        if new_status == 'COMPLETED':
            self.is_locked = True
        else:
            # Unlock if not completed (allows edits)
            self.is_locked = False
        # Save only status and is_locked fields
        self.save(update_fields=['status', 'is_locked'])
    
    def save(self, *args, **kwargs):
        """
        Auto-recalculate status before saving.
        Skip recalculation if explicitly requested (e.g., during migration) or if update_fields is specified.
        """
        skip_recalculate = kwargs.pop('skip_recalculate', False)
        update_fields = kwargs.get('update_fields', None)
        
        if not skip_recalculate and not update_fields:
            # Recalculate status based on sign-off flags
            # Only recalculate if not using update_fields (to avoid recursion)
            if not self.preparer_signed:
                self.status = 'OPEN'
            elif self.preparer_signed and not self.reviewer_signed:
                self.status = 'READY_FOR_REVIEW'
            else:
                self.status = 'COMPLETED'
            
            # Auto-lock when completed
            if self.status == 'COMPLETED':
                self.is_locked = True
            else:
                self.is_locked = False
        # Call parent save
        super().save(*args, **kwargs)


class Questionnaire(models.Model):
    """
    Questionnaire for collecting structured answers from clients/auditors.
    Maps answers to standard controls and auto-generates Sheet rows.
    """
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Open', 'Open'),
        ('Completed', 'Completed'),
    ]
    name = models.CharField(max_length=200, help_text="Questionnaire name")
    engagement = models.ForeignKey(Engagement, on_delete=models.CASCADE, related_name='questionnaires')
    standard = models.ForeignKey(Standard, on_delete=models.CASCADE, related_name='questionnaires')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')
    respondent = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='questionnaires')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        unique_together = [['engagement', 'standard', 'name']]
    
    def __str__(self):
        return f"{self.name} - {self.standard.name} ({self.engagement.title})"
    
    def get_completion_percentage(self):
        """Calculate completion percentage based on answered questions"""
        total = self.questions.count()
        if total == 0:
            return 0
        answered = self.responses.filter(answer__isnull=False).count()
        return int((answered / total) * 100)


class QuestionnaireQuestion(models.Model):
    """
    Question in a questionnaire, linked to a StandardControl.
    """
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE, related_name='questions')
    control = models.ForeignKey(StandardControl, on_delete=models.CASCADE, related_name='questionnaire_questions')
    question_text = models.TextField(help_text="Question text (defaults to control description)")
    order = models.IntegerField(default=0, help_text="Display order")
    
    class Meta:
        ordering = ['order', 'control__control_id']
        unique_together = [['questionnaire', 'control']]
    
    def __str__(self):
        return f"{self.questionnaire.name} - {self.control.control_id}"
    
    def save(self, *args, **kwargs):
        # Auto-set question_text from control if not provided
        if not self.question_text:
            self.question_text = self.control.control_description
        super().save(*args, **kwargs)


class QuestionnaireResponse(models.Model):
    """
    Response to a questionnaire question.
    """
    ANSWER_CHOICES = [
        ('Yes', 'Yes'),
        ('No', 'No'),
        ('NA', 'N/A'),
    ]
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(QuestionnaireQuestion, on_delete=models.CASCADE, related_name='responses')
    answer = models.CharField(max_length=10, choices=ANSWER_CHOICES, null=True, blank=True)
    response_text = models.TextField(blank=True, help_text="Optional comment/notes")
    answered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    answered_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['question__order']
        unique_together = [['questionnaire', 'question']]
    
    def __str__(self):
        return f"{self.questionnaire.name} - {self.question.control.control_id}: {self.answer or 'Not answered'}"


# Keep QuestionnaireResponseSet for backward compatibility (deprecated)
class QuestionnaireResponseSet(models.Model):
    """Deprecated - use Questionnaire instead"""
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Open', 'Open'),
        ('Completed', 'Completed'),
    ]
    engagement = models.ForeignKey(Engagement, on_delete=models.CASCADE, related_name='questionnaire_response_sets')
    standard = models.ForeignKey(Standard, on_delete=models.CASCADE, related_name='questionnaire_response_sets')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = [['engagement', 'standard']]
    
    def __str__(self):
        return f"Questionnaire - {self.standard.name} ({self.engagement.title})"

class RequestDocument(models.Model):
    DOC_TYPE_CHOICES = [
        ('evidence', 'Evidence'),
        ('workpaper', 'Workpaper'),
    ]

    FOLDER_CHOICES = [
        ('project_admin', '01. Project Admin'),
        ('report_templates', 'Report Templates'),
        ('reports', 'Reports'),
        ('workplan', 'Workplan'),
        ('evidence', 'Evidence'),
        ('screenshots', 'Screenshots'),
        ('policies', 'Policies'),
        ('logs', 'Logs'),
        ('other', 'Other'),
    ]
    # Request is optional - documents can be uploaded directly without a Request
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='documents', null=True, blank=True)
    # Engagement is required - all documents must belong to an engagement
    engagement = models.ForeignKey(Engagement, on_delete=models.CASCADE, related_name='documents')
    # Standard is required - all documents must belong to a standard (via control)
    standard = models.ForeignKey(Standard, on_delete=models.CASCADE, related_name='documents', null=True, blank=True)
    # For documents linked to controls (from Requests/Sheets)
    linked_control = models.ForeignKey(EngagementControl, on_delete=models.SET_NULL, null=True, blank=True, related_name='documents')
    file = models.FileField(upload_to='request_docs/%Y/%m/%d/')
    doc_type = models.CharField(max_length=20, choices=DOC_TYPE_CHOICES, default='workpaper')
    folder = models.CharField(max_length=30, choices=FOLDER_CHOICES, default='workplan')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.doc_type} - {self.file.name}"
    
    def get_file_name(self):
        """Return just the filename without path"""
        import os
        return os.path.basename(self.file.name)
    
    @property
    def source(self):
        """Determine document source: manual, request, or sheet"""
        if self.request:
            if self.doc_type == 'evidence':
                return 'request'
            elif self.doc_type == 'workpaper':
                return 'sheet'
        return 'manual'
    
    @property
    def is_read_only(self):
        """Check if document is read-only (from request or sheet)"""
        return self.source in ['request', 'sheet']
    
    def save(self, *args, **kwargs):
        # Auto-set engagement from request if not set
        if not self.engagement and self.request and self.request.linked_control:
            self.engagement = self.request.linked_control.engagement
        # Auto-set linked_control from request if not set
        if not self.linked_control and self.request:
            self.linked_control = self.request.linked_control
        # Auto-set standard from control if not set
        if not self.standard and self.linked_control and self.linked_control.standard_control:
            self.standard = self.linked_control.standard_control.standard
        # Ensure engagement is set - required field
        if not self.engagement:
            if self.linked_control:
                self.engagement = self.linked_control.engagement
            else:
                raise ValidationError("Document must have an engagement. Set engagement or linked_control.")
        super().save(*args, **kwargs)
