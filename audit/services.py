"""
Business logic services for GRC/Audit platform.
Handles auto-generation of controls from standards and questionnaires.
"""
from django.db import transaction
from .models import Engagement, EngagementControl, StandardControl


def generate_engagement_controls(engagement):
    """
    Auto-generate EngagementControl rows from selected standards.
    
    Business Rule:
    - Fetches all StandardControls from engagement.standards
    - Creates one EngagementControl per StandardControl
    - Skips controls that already exist (by control_id)
    - Marks source='auto' and links to StandardControl
    
    Returns:
        tuple: (created_count, skipped_count)
    """
    if not engagement.standards.exists():
        return 0, 0
    
    created_count = 0
    skipped_count = 0
    
    with transaction.atomic():
        # Get all standard controls from selected standards
        standard_controls = StandardControl.objects.filter(
            standard__in=engagement.standards.all(),
            is_active=True
        ).select_related('standard')
        
        for sc in standard_controls:
            # Use get_or_create to avoid duplicates
            # Key: engagement + control_id (unique together)
            control, created = EngagementControl.objects.get_or_create(
                engagement=engagement,
                control_id=sc.control_id,
                defaults={
                    'standard_control': sc,
                    'control_name': sc.title or sc.control_id,  # Use title if available, fallback to control_id
                    'control_description': sc.control_description,
                    'testing_procedure': sc.default_testing_type or '',  # Deprecated field
                    'test_applied': '',  # Empty - auditor fills this
                    'test_performed': '',  # Empty - auditor fills this
                    'test_results': '',  # Empty - auditor fills this
                    'source': 'auto',
                }
            )
            
            if created:
                created_count += 1
            else:
                skipped_count += 1
    
    return created_count, skipped_count


def create_engagement_with_controls(client_name, title, audit_year, standard_ids, lead_auditor=None):
    """
    Create an engagement and auto-generate controls from selected standards.
    
    This is the primary entry point for engagement creation.
    Business logic ensures controls are always generated from standards.
    
    Args:
        client_name: Client name
        title: Engagement title
        audit_year: Audit year
        standard_ids: List of Standard IDs to use
        lead_auditor: Optional User object
    
    Returns:
        Engagement instance
    """
    from .models import Standard
    
    with transaction.atomic():
        # Create engagement
        engagement = Engagement.objects.create(
            title=title,
            client_name=client_name,
            audit_year=audit_year,
            lead_auditor=lead_auditor
        )
        
        # Add standards - this will trigger the m2m_changed signal
        # which automatically generates EngagementControl rows
        standards = Standard.objects.filter(id__in=standard_ids)
        engagement.standards.set(standards)
        
        # Signal has already generated controls, but we can get the count for reporting
        # Refresh from DB to get accurate count
        engagement.refresh_from_db()
        created_count = EngagementControl.objects.filter(
            engagement=engagement,
            source='auto'
        ).count()
        
        return engagement, created_count, 0


def generate_sheets_from_questionnaire(questionnaire):
    """
    Auto-generate Sheet rows (EngagementControl) from questionnaire responses.
    
    Business Rule (AuditSource Workplan):
    - For each QuestionnaireResponse with an answer:
      - Check if Sheet row exists for (engagement + control_id)
      - If NOT exists: Create Sheet row with:
        - control_id from StandardControl
        - control_description from StandardControl
        - standard_control FK
        - engagement from questionnaire.engagement
        - status = 'Open'
        - source = 'questionnaire'
        - test_applied = EMPTY (auditor fills this)
        - test_performed = EMPTY (auditor fills this)
        - test_results = EMPTY (auditor fills this)
      - If exists: Do NOT update (prevent overwriting auditor work)
    
    IMPORTANT: Questionnaire responses are NOT written into Test Performed.
    Sheets represent auditor workpapers, not questionnaire results.
    Questionnaire responses are displayed as read-only reference only.
    
    Prevents duplicates using get_or_create with unique constraint on (engagement, control_id).
    
    Returns:
        int: Number of sheet rows created (not updated)
    """
    from .models import QuestionnaireResponse
    import logging
    
    logger = logging.getLogger(__name__)
    
    engagement = questionnaire.engagement
    standard = questionnaire.standard
    created_count = 0
    
    # Get all responses with answers
    responses = QuestionnaireResponse.objects.filter(
        questionnaire=questionnaire,
        answer__isnull=False
    ).select_related('question', 'question__control')
    
    if not responses.exists():
        logger.warning(f'No answered questions found for questionnaire {questionnaire.id}')
        return 0
    
    for response in responses:
        control = response.question.control
        
        # Check if Sheet row already exists for this engagement + control_id
        # Use get_or_create to prevent duplicates (unique_together constraint)
        sheet_row, created = EngagementControl.objects.get_or_create(
            engagement=engagement,
            control_id=control.control_id,
            defaults={
                'standard_control': control,
                'control_name': control.title or control.control_id,  # Use title if available, fallback to control_id
                'control_description': control.control_description,
                'test_applied': '',  # Empty - auditor fills this
                'test_performed': '',  # Empty - auditor fills this (NOT from questionnaire)
                'test_results': '',  # Empty - auditor fills this
                'source': 'questionnaire'
            }
        )
        
        if created:
            created_count += 1
            logger.info(f'Created Sheet row for control {control.control_id} from questionnaire {questionnaire.id}')
        else:
            # Do NOT update existing rows - sheets are auditor workpapers
            # If row already exists, it means it was created from standard or manually
            # We preserve auditor work and do not overwrite
            logger.info(f'Sheet row for control {control.control_id} already exists - skipping (preserving auditor work)')
    
    logger.info(f'Questionnaire {questionnaire.id}: {created_count} sheet rows created')
    return created_count
