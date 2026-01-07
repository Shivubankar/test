from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, FileResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.urls import reverse
from .models import Engagement, EngagementControl, Request, RequestDocument, Standard, StandardControl, Questionnaire, QuestionnaireQuestion, QuestionnaireResponse
from .services import generate_engagement_controls, create_engagement_with_controls
from .forms import EvidenceUploadForm, WorkpaperUploadForm, RequestReviewForm
import os
from functools import wraps
from django.utils import timezone


ROLE_ADMIN = 'Admin'
ROLE_CONTROL_ASSESSOR = 'Control Assessor'
ROLE_CONTROL_REVIEWER = 'Control Reviewer'
ROLE_CLIENT = 'Client'


def get_user_role(user):
    """Determine user role based on groups or superuser status."""
    if user.is_superuser:
        return ROLE_ADMIN

    # Priority ordering to resolve multiple group membership
    if user.groups.filter(name=ROLE_ADMIN).exists():
        return ROLE_ADMIN
    if user.groups.filter(name=ROLE_CONTROL_ASSESSOR).exists():
        return ROLE_CONTROL_ASSESSOR
    if user.groups.filter(name=ROLE_CONTROL_REVIEWER).exists():
        return ROLE_CONTROL_REVIEWER
    if user.groups.filter(name=ROLE_CLIENT).exists():
        return ROLE_CLIENT

    # Default to least-privileged role
    return ROLE_CLIENT


def user_in_roles(user, roles):
    """Convenience helper to check membership against allowed roles."""
    return get_user_role(user) in roles


def role_required(allowed_roles):
    """Decorator to restrict view access based on group role."""
    def decorator(view_func):
        @login_required
        def _wrapped(request, *args, **kwargs):
            if not user_in_roles(request.user, allowed_roles):
                messages.error(request, 'Permission denied.')
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


def role_required(roles):
    """Decorator to enforce role-based access on views."""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if user_in_roles(request.user, roles):
                return view_func(request, *args, **kwargs)
            messages.error(request, 'Permission denied.')
            return redirect('dashboard')
        return _wrapped_view
    return decorator


@login_required
def sheets(request):
    """
    Sheets module - displays EngagementControl rows (auto-generated from Standards).
    No manual creation of controls allowed here.
    """
    engagement_id = request.GET.get('engagement')
    
    if engagement_id:
        engagement = get_object_or_404(Engagement, id=engagement_id)
        controls = EngagementControl.objects.filter(engagement=engagement).select_related('engagement', 'standard_control')
    else:
        engagement = Engagement.objects.first()
        if engagement:
            controls = EngagementControl.objects.filter(engagement=engagement).select_related('engagement', 'standard_control')
        else:
            controls = EngagementControl.objects.none()
    
    # Get all requests for these controls
    requests = Request.objects.filter(linked_control__in=controls).select_related(
        'linked_control', 'assignee', 'prepared_by', 'reviewed_by'
    )
    
    # Create a dict for quick lookup
    requests_dict = {req.linked_control.id: req for req in requests}
    
    # Create control-request pairs for template
    control_requests = []
    for control in controls:
        control_requests.append({
            'control': control,
            'request': requests_dict.get(control.id)
        })
    
    engagements = Engagement.objects.all()
    user_role = get_user_role(request.user)
    is_control_assessor = request.user.groups.filter(name=ROLE_CONTROL_ASSESSOR).exists()
    is_control_reviewer = request.user.groups.filter(name=ROLE_CONTROL_REVIEWER).exists()
    is_client = request.user.groups.filter(name=ROLE_CLIENT).exists()
    is_admin_user = request.user.is_superuser
    
    context = {
        'engagement': engagement,
        'engagements': engagements,
        'control_requests': control_requests,
        'user_role': user_role,
        'can_upload_evidence': is_admin_user or is_control_assessor or is_control_reviewer or is_client,
        'can_upload_workpaper': is_admin_user or is_control_assessor or is_control_reviewer,
        # Sign-off permissions are role-only; enabled per role
        'can_sign_preparer': is_admin_user or is_control_assessor,
        'can_sign_reviewer': is_admin_user or is_control_reviewer,
        'can_sign_admin': is_admin_user,
    }
    
    return render(request, 'audit/sheets.html', context)


@login_required
def dashboard(request):
    """
    High-level engagement summary dashboard.
    Shows completion percentages for rows, documents, requests, and tasks.
    """
    engagement_id = request.GET.get('engagement')
    
    if engagement_id:
        engagement = get_object_or_404(Engagement, id=engagement_id)
    else:
        engagement = Engagement.objects.first()
    
    if engagement:
        # Get all controls for the engagement
        all_controls = EngagementControl.objects.filter(engagement=engagement)
        total_controls = all_controls.count()
        
        # Get all requests for these controls
        all_requests = Request.objects.filter(linked_control__in=all_controls)
        
        # Calculate Row Sign-offs % (Accepted requests)
        accepted_requests = all_requests.filter(status='Accepted').count()
        row_signoffs_percent = (accepted_requests / total_controls * 100) if total_controls > 0 else 0
        
        # Calculate Document Sign-offs % (Requests with documents)
        requests_with_docs = all_requests.filter(documents__isnull=False).distinct().count()
        doc_signoffs_percent = (requests_with_docs / total_controls * 100) if total_controls > 0 else 0
        
        # Calculate Requests Completion % (Non-Open requests)
        completed_requests = all_requests.exclude(status='Open').count()
        requests_completion_percent = (completed_requests / total_controls * 100) if total_controls > 0 else 0
        
        # Calculate Tasks Completion % (Requests with test notes)
        requests_with_notes = all_requests.exclude(auditor_test_notes__isnull=True).exclude(auditor_test_notes='').count()
        tasks_completion_percent = (requests_with_notes / total_controls * 100) if total_controls > 0 else 0
        
        # Get recent activity
        recent_requests = all_requests.select_related('linked_control', 'reviewed_by').order_by('-updated_at')[:10]
        
    else:
        total_controls = 0
        row_signoffs_percent = 0
        doc_signoffs_percent = 0
        requests_completion_percent = 0
        tasks_completion_percent = 0
        recent_requests = []
    
    engagements = Engagement.objects.all()
    user_role = get_user_role(request.user)
    
    context = {
        'engagement': engagement,
        'engagements': engagements,
        'user_role': user_role,
        'total_controls': total_controls,
        'row_signoffs_percent': round(row_signoffs_percent, 1),
        'doc_signoffs_percent': round(doc_signoffs_percent, 1),
        'requests_completion_percent': round(requests_completion_percent, 1),
        'tasks_completion_percent': round(tasks_completion_percent, 1),
        'recent_requests': recent_requests,
    }
    
    return render(request, 'audit/dashboard.html', context)


@login_required
def forms(request):
    """
    Structured audit forms module.
    Supports forms like Client Profile, SOC 2 Scope, Section III.
    Forms support save as draft, sign-off, reviewer approval, and link to engagements.
    """
    engagement_id = request.GET.get('engagement')
    
    if engagement_id:
        engagement = get_object_or_404(Engagement, id=engagement_id)
    else:
        engagement = Engagement.objects.first()
    
    engagements = Engagement.objects.all()
    user_role = get_user_role(request.user)
    
    context = {
        'engagement': engagement,
        'engagements': engagements,
        'user_role': user_role,
    }
    
    return render(request, 'audit/forms.html', context)


@login_required
def questionnaires(request):
    """
    Questionnaires list page.
    Shows questionnaires per engagement with Name, Respondent, Status, Last Updated.
    """
    engagement_id = request.GET.get('engagement')
    
    if engagement_id:
        engagement = get_object_or_404(Engagement, id=engagement_id)
    else:
        engagement = Engagement.objects.first()
    
    engagements = Engagement.objects.all()
    user_role = get_user_role(request.user)
    
    # List questionnaires for this engagement
    from .models import Questionnaire
    questionnaires_list = Questionnaire.objects.filter(engagement=engagement).select_related(
        'standard', 'respondent', 'engagement'
    ) if engagement else Questionnaire.objects.none()
    
    context = {
        'engagement': engagement,
        'engagements': engagements,
        'user_role': user_role,
        'questionnaires': questionnaires_list,
    }
    
    return render(request, 'audit/questionnaires.html', context)

@login_required
@require_http_methods(["GET", "POST"])
@role_required([ROLE_ADMIN, ROLE_CONTROL_ASSESSOR])
def create_questionnaire(request, engagement_id):
    """
    Create a new Questionnaire.
    Step 1: Select Engagement (from URL)
    Step 2: Select Standard
    Step 3: Auto-load Standard Controls as questions
    Step 4: Save as Draft
    """
    engagement = get_object_or_404(Engagement, id=engagement_id)
    
    if request.method == 'POST':
        standard_id = request.POST.get('standard_id')
        name = request.POST.get('name', '').strip()
        
        if not standard_id:
            messages.error(request, 'Please select a standard.')
            return redirect(f"{reverse('questionnaires')}?engagement={engagement.id}")
        
        if not name:
            messages.error(request, 'Please provide a questionnaire name.')
            return redirect(f"{reverse('questionnaires')}?engagement={engagement.id}")
        
        standard = get_object_or_404(Standard, id=standard_id)
        
        # Create questionnaire
        from .models import Questionnaire, QuestionnaireQuestion, StandardControl
        questionnaire = Questionnaire.objects.create(
            name=name,
            engagement=engagement,
            standard=standard,
            status='Draft',
            respondent=request.user
        )
        
        # Auto-load Standard Controls as questions
        standard_controls = StandardControl.objects.filter(standard=standard, is_active=True).order_by('control_id')
        question_count = 0
        for idx, sc in enumerate(standard_controls):
            QuestionnaireQuestion.objects.create(
                questionnaire=questionnaire,
                control=sc,
                question_text=sc.control_description,
                order=idx + 1
            )
            question_count += 1
        
        messages.success(request, f'Questionnaire "{name}" created with {question_count} questions. You can now answer the questions.')
        return redirect(f"{reverse('questionnaire_detail', args=[questionnaire.id])}")
    
    # GET request - show create form
    standards = Standard.objects.all()
    context = {
        'engagement': engagement,
        'standards': standards,
    }
    return render(request, 'audit/create_questionnaire.html', context)


@login_required
def questionnaire_detail(request, questionnaire_id):
    """
    Questionnaire detail page for answering questions.
    Shows Control ID, Question text, Answer options (Yes/No/NA), Optional comment box.
    """
    from .models import Questionnaire, QuestionnaireResponse
    questionnaire = get_object_or_404(Questionnaire, id=questionnaire_id)
    
    user_role = get_user_role(request.user)
    
    # Check permissions
    can_edit = user_in_roles(request.user, [ROLE_ADMIN, ROLE_CONTROL_ASSESSOR, ROLE_CLIENT])
    can_submit = user_in_roles(request.user, [ROLE_ADMIN, ROLE_CONTROL_ASSESSOR])
    
    # Get all questions with their responses
    questions = questionnaire.questions.all()
    responses_dict = {}
    for response in QuestionnaireResponse.objects.filter(questionnaire=questionnaire).select_related('question'):
        responses_dict[response.question_id] = response
    
    # Create question-response pairs for template
    question_responses = []
    for question in questions:
        question_responses.append({
            'question': question,
            'response': responses_dict.get(question.id)
        })
    
    # Handle POST - save responses
    if request.method == 'POST' and can_edit:
        action = request.POST.get('action')
        
        if action == 'save_draft':
            # Save individual responses
            for qr in question_responses:
                question = qr['question']
                answer = request.POST.get(f'answer_{question.id}')
                response_text = request.POST.get(f'response_text_{question.id}', '').strip()
                
                if answer:
                    response, created = QuestionnaireResponse.objects.get_or_create(
                        questionnaire=questionnaire,
                        question=question,
                        defaults={'answered_by': request.user}
                    )
                    response.answer = answer
                    response.response_text = response_text
                    response.answered_by = request.user
                    response.save()
            
            questionnaire.status = 'Draft'
            questionnaire.save()
            messages.success(request, 'Questionnaire saved as draft.')
            return redirect(f"{reverse('questionnaire_detail', args=[questionnaire.id])}")
        
        elif action == 'submit' and can_submit:
            # Wrap entire submission in transaction for safety
            from django.db import transaction
            from .services import generate_sheets_from_questionnaire
            import logging
            
            logger = logging.getLogger(__name__)
            
            try:
                with transaction.atomic():
                    # Step 1: Save all responses first
                    answered_count = 0
                    for qr in question_responses:
                        question = qr['question']
                        answer = request.POST.get(f'answer_{question.id}')
                        response_text = request.POST.get(f'response_text_{question.id}', '').strip()
                        
                        if answer:
                            response, created = QuestionnaireResponse.objects.get_or_create(
                                questionnaire=questionnaire,
                                question=question,
                                defaults={'answered_by': request.user}
                            )
                            response.answer = answer
                            response.response_text = response_text
                            response.answered_by = request.user
                            response.save()
                            answered_count += 1
                    
                    if answered_count == 0:
                        messages.warning(request, 'Please answer at least one question before submitting.')
                        return redirect(f"{reverse('questionnaire_detail', args=[questionnaire.id])}")
                    
                    # Step 2: Auto-generate Sheets from responses
                    sheets_created = generate_sheets_from_questionnaire(questionnaire)
                    
                    # Step 3: Update questionnaire status to Completed
                    questionnaire.status = 'Completed'
                    questionnaire.save()
                    
                    logger.info(f'Questionnaire {questionnaire.id} submitted. {sheets_created} sheet rows created.')
                    
                    messages.success(request, f'Questionnaire submitted successfully. {sheets_created} sheet row(s) generated.')
                    # Redirect to Sheets page filtered by engagement
                    return redirect(f"{reverse('sheets')}?engagement={questionnaire.engagement.id}")
                    
            except Exception as e:
                logger.error(f'Error submitting questionnaire {questionnaire.id}: {str(e)}', exc_info=True)
                messages.error(request, f'Error submitting questionnaire: {str(e)}. Please try again or contact support.')
                return redirect(f"{reverse('questionnaire_detail', args=[questionnaire.id])}")
    
    context = {
        'questionnaire': questionnaire,
        'question_responses': question_responses,
        'user_role': user_role,
        'can_edit': can_edit,
        'can_submit': can_submit,
    }
    
    return render(request, 'audit/questionnaire_detail.html', context)


@login_required
@require_http_methods(["POST"])
@role_required([ROLE_ADMIN, ROLE_CONTROL_ASSESSOR, ROLE_CONTROL_REVIEWER])
def update_control(request, control_id):
    """
    Update control fields: test_applied, test_performed, test_results.
    Status is backend-controlled and computed from conditions.
    """
    control = get_object_or_404(EngagementControl, id=control_id)
    
    test_applied = request.POST.get(f'test_applied_{control.id}', '').strip()
    test_performed = request.POST.get(f'test_performed_{control.id}', '').strip()
    test_results = request.POST.get(f'test_results_{control.id}', '').strip()
    
    # Update fields (allow empty strings for test_performed and test_results)
    if test_applied is not None:
        control.test_applied = test_applied
    if test_performed is not None:  # Allow empty string - auditor fills this
        control.test_performed = test_performed
    if test_results is not None:  # Allow empty string - auditor fills this
        control.test_results = test_results
    
    control.save()
    messages.success(request, f'Control {control.control_id} updated successfully.')
    
    return redirect(f"{reverse('sheets')}?engagement={control.engagement.id}")


@login_required
@require_http_methods(["POST"])
@role_required([ROLE_ADMIN, ROLE_CONTROL_ASSESSOR, ROLE_CONTROL_REVIEWER])
def upload_workpaper_control(request, control_id):
    """
    Upload workpaper documents directly to a control (not via request).
    """
    control = get_object_or_404(EngagementControl, id=control_id)
    
    workpaper_files = request.FILES.getlist('workpaper_files')
    
    if not workpaper_files:
        messages.error(request, 'Please select at least one file to upload.')
        return redirect(f"{reverse('sheets')}?engagement={control.engagement.id}")
    
    uploaded_count = 0
    for file in workpaper_files:
        RequestDocument.objects.create(
            engagement=control.engagement,
            linked_control=control,
            file=file,
            doc_type='workpaper',
            folder='workplan',
            uploaded_by=request.user
        )
        uploaded_count += 1
    
    messages.success(request, f'{uploaded_count} workpaper file(s) uploaded successfully.')
    return redirect(f"{reverse('sheets')}?engagement={control.engagement.id}")


@login_required
@require_http_methods(["POST"])
def signoff_control(request, control_id):
    """
    Record a sign-off on a control by role. No sequencing, always enabled by permission.
    role param: preparer | reviewer | admin
    """
    control = get_object_or_404(EngagementControl, id=control_id)
    role = request.POST.get('role')
    now = timezone.now()
    
    # Permission gating: user must have the corresponding role
    if role == 'preparer':
        if not user_in_roles(request.user, [ROLE_ADMIN, ROLE_CONTROL_ASSESSOR]):
            messages.error(request, 'You do not have permission to sign as Preparer.')
            return redirect(f"{reverse('sheets')}?engagement={control.engagement.id}")
        control.preparer_signed_by = request.user
        control.preparer_signed_at = now
    elif role == 'reviewer':
        if not user_in_roles(request.user, [ROLE_ADMIN, ROLE_CONTROL_REVIEWER]):
            messages.error(request, 'You do not have permission to sign as Reviewer.')
            return redirect(f"{reverse('sheets')}?engagement={control.engagement.id}")
        control.reviewer_signed_by = request.user
        control.reviewer_signed_at = now
    elif role == 'admin':
        if not user_in_roles(request.user, [ROLE_ADMIN]):
            messages.error(request, 'Only Admins can perform Admin sign-off.')
            return redirect(f"{reverse('sheets')}?engagement={control.engagement.id}")
        control.admin_signed_by = request.user
        control.admin_signed_at = now
    else:
        messages.error(request, 'Invalid sign-off role.')
        return redirect(f"{reverse('sheets')}?engagement={control.engagement.id}")
    
    control.save()
    messages.success(request, 'Sign-off recorded.')
    return redirect(f"{reverse('sheets')}?engagement={control.engagement.id}")


@login_required
def requests_list(request):
    """
    Central evidence request tracker.
    Shows requests with Key, Status, Title, Description, Due date, Owner, Tags.
    Status lifecycle: Open, Ready for Review (In-Review), Changes Requested (Returned), Completed (Accepted).
    Includes status counts and search by title/description/tags.
    """
    engagement_id = request.GET.get('engagement')
    status_filter = request.GET.get('status')
    q = request.GET.get('q', '').strip()
    
    if engagement_id:
        engagement = get_object_or_404(Engagement, id=engagement_id)
        controls = EngagementControl.objects.filter(engagement=engagement)
        all_requests = Request.objects.filter(linked_control__in=controls).select_related(
            'linked_control', 'assignee', 'prepared_by', 'reviewed_by'
        )
    else:
        engagement = Engagement.objects.first()
        if engagement:
            controls = EngagementControl.objects.filter(engagement=engagement)
            all_requests = Request.objects.filter(linked_control__in=controls).select_related(
                'linked_control', 'assignee', 'prepared_by', 'reviewed_by'
            )
        else:
            all_requests = Request.objects.none()
    
    # Filter by status if provided
    if status_filter:
        all_requests = all_requests.filter(status=status_filter)
    
    # Text search - search by control ID, title, description, tags, and owner
    if q:
        from django.db.models import Q
        all_requests = all_requests.filter(
            Q(title__icontains=q) | 
            Q(description__icontains=q) | 
            Q(tags__icontains=q) |
            Q(linked_control__control_id__icontains=q) |
            Q(assignee__username__icontains=q) |
            Q(assignee__first_name__icontains=q) |
            Q(assignee__last_name__icontains=q)
        )
    
    # Counts for chips - Use Django-safe keys (uppercase with underscores)
    # Database still uses 'In-Review', 'Returned', 'Accepted' as status values
    counts = {
        'All': Request.objects.filter(linked_control__in=controls).count() if engagement else 0,
        'Open': Request.objects.filter(linked_control__in=controls, status='Open').count() if engagement else 0,
        'IN_REVIEW': Request.objects.filter(linked_control__in=controls, status='In-Review').count() if engagement else 0,
        'RETURNED': Request.objects.filter(linked_control__in=controls, status='Returned').count() if engagement else 0,
        'ACCEPTED': Request.objects.filter(linked_control__in=controls, status='Accepted').count() if engagement else 0,
    }
    
    # Prefetch document counts for each request
    from django.db.models import Count, Q
    all_requests = all_requests.annotate(
        evidence_count=Count('documents', filter=Q(documents__doc_type='evidence')),
        workpaper_count=Count('documents', filter=Q(documents__doc_type='workpaper'))
    )
    
    engagements = Engagement.objects.all()
    user_role = get_user_role(request.user)
    
    context = {
        'engagement': engagement,
        'engagements': engagements,
        'user_role': user_role,
        'requests': all_requests.order_by('-updated_at'),
        'status_filter': status_filter,
        'q': q,
        'counts': counts,
    }
    
    return render(request, 'audit/requests_list.html', context)

@login_required
@require_http_methods(["POST"])
@role_required([ROLE_ADMIN, ROLE_CONTROL_ASSESSOR, ROLE_CONTROL_REVIEWER])
def create_request(request, control_id):
    """
    Create a Request from a Sheet row (control).
    Each request links to exactly one control.
    Requests are used to collect evidence from Clients.
    Supports title, description, due_date, and tags from form.
    """
    try:
        control = get_object_or_404(EngagementControl, id=control_id)
        
        # Check if request already exists
        existing_request = control.requests.first()
        if existing_request:
            messages.info(request, 'A request already exists for this control.')
        else:
            # Get form data
            title = request.POST.get('title', '').strip()
            description = request.POST.get('description', '').strip()
            due_date = request.POST.get('due_date', '').strip()
            tags = request.POST.get('tags', '').strip()
            
            # Use defaults if not provided
            if not title:
                title = f"Evidence Request for {control.control_id}"
            if not description:
                description = f"Please provide evidence for control {control.control_id}: {control.control_description[:100]}"
            
            # Create new request
            new_request = Request.objects.create(
                linked_control=control,
                assignee=control.engagement.lead_auditor,
                status='Open',
                title=title,
                description=description,
                due_date=due_date if due_date else None,
                tags=tags
            )
            messages.success(request, 'Request created successfully.')
        
        engagement_id = control.engagement.id
        return redirect(f"{reverse('requests_list')}?engagement={engagement_id}")
    except Exception as e:
        messages.error(request, f'Error creating request: {str(e)}')
        return redirect('requests_list')


@login_required
def documents(request):
    """
    Central document repository matching AuditSource 2.0.
    Supports folder-based filtering, direct uploads, and aggregates documents from Requests/Sheets.
    """
    engagement_id = request.GET.get('engagement')
    folder = request.GET.get('folder', 'all')
    q = request.GET.get('q', '').strip()
    sort_by = request.GET.get('sort', 'updated')  # updated, name
    
    user_role = get_user_role(request.user)
    
    # Clients can view but not upload
    can_upload = user_in_roles(request.user, [ROLE_ADMIN, ROLE_CONTROL_ASSESSOR, ROLE_CONTROL_REVIEWER])
    can_delete = user_in_roles(request.user, [ROLE_ADMIN, ROLE_CONTROL_ASSESSOR, ROLE_CONTROL_REVIEWER])
    
    if engagement_id:
        engagement = get_object_or_404(Engagement, id=engagement_id)
    else:
        engagement = Engagement.objects.first()
    
    # Get all documents for the engagement
    # Documents can come from:
    # 1. RequestDocument with engagement FK (direct uploads)
    # 2. RequestDocument with request FK (from Requests/Sheets)
    if engagement:
        from django.db.models import Q
        
        # Build query: documents with engagement OR documents via requests
        controls = EngagementControl.objects.filter(engagement=engagement)
        requests = Request.objects.filter(linked_control__in=controls)
        
        # Use Q objects to combine queries properly
        all_documents = RequestDocument.objects.filter(
            Q(engagement=engagement) | Q(request__in=requests)
        ).select_related(
            'request', 'request__linked_control', 'linked_control', 'uploaded_by', 'engagement'
        ).distinct()
        
        # Backfill engagement for documents that don't have it (one-time fix)
        docs_to_fix = all_documents.filter(engagement__isnull=True)
        for doc in docs_to_fix:
            if doc.request and doc.request.linked_control:
                doc.engagement = doc.request.linked_control.engagement
                doc.save(update_fields=['engagement'])
        
        # Re-query after backfill to ensure we have all documents
        all_documents = RequestDocument.objects.filter(
            Q(engagement=engagement) | Q(request__in=requests)
        ).select_related(
            'request', 'request__linked_control', 'linked_control', 'uploaded_by', 'engagement'
        ).distinct()
    else:
        all_documents = RequestDocument.objects.none()
    
    # Filter by folder (AuditSource folder structure)
    if folder != 'all':
        all_documents = all_documents.filter(folder=folder)
    
    # Search by filename, control ID, or request title
    if q:
        from django.db.models import Q
        all_documents = all_documents.filter(
            Q(file__icontains=q) | 
            Q(linked_control__control_id__icontains=q) |
            Q(request__linked_control__control_id__icontains=q) |
            Q(request__title__icontains=q)
        )
    
    # Sort
    if sort_by == 'name':
        all_documents = all_documents.order_by('file')
    else:
        all_documents = all_documents.order_by('-updated_at')
    
    # Evaluate queryset to list for template (ensures it's not empty due to lazy evaluation)
    # Add source and is_read_only properties to each document
    documents_list = []
    for doc in all_documents:
        documents_list.append(doc)
    
    # Folder counts for sidebar (use same query pattern)
    if engagement:
        from django.db.models import Q
        controls = EngagementControl.objects.filter(engagement=engagement)
        requests = Request.objects.filter(linked_control__in=controls)
        
        folder_counts = {
            'project_admin': RequestDocument.objects.filter(
                (Q(engagement=engagement) | Q(request__in=requests)) & Q(folder='project_admin')
            ).distinct().count(),
            'report_templates': RequestDocument.objects.filter(
                (Q(engagement=engagement) | Q(request__in=requests)) & Q(folder='report_templates')
            ).distinct().count(),
            'reports': RequestDocument.objects.filter(
                (Q(engagement=engagement) | Q(request__in=requests)) & Q(folder='reports')
            ).distinct().count(),
            'workplan': RequestDocument.objects.filter(
                (Q(engagement=engagement) | Q(request__in=requests)) & Q(folder='workplan')
            ).distinct().count(),
        }
    else:
        folder_counts = {'project_admin': 0, 'report_templates': 0, 'reports': 0, 'workplan': 0}
    
    engagements = Engagement.objects.all()
    
    context = {
        'engagement': engagement,
        'engagements': engagements,
        'user_role': user_role,
        'documents': documents_list,  # Use evaluated list
        'folder': folder,
        'q': q,
        'sort_by': sort_by,
        'folder_counts': folder_counts,
        'can_upload': can_upload,
        'can_delete': can_delete,
    }
    
    return render(request, 'audit/documents.html', context)

@login_required
@require_http_methods(["POST"])
def documents_upload(request):
    """
    Upload documents directly to Documents repository.
    Requires: engagement_id, folder, files.
    Documents are classified by folder (Workplan=Workpapers, Reports=Reports, etc.)
    """
    user_role = get_user_role(request.user)
    
    # Only Admin, Assessor, Reviewer can upload directly
    if not user_in_roles(request.user, [ROLE_ADMIN, ROLE_CONTROL_ASSESSOR, ROLE_CONTROL_REVIEWER]):
        messages.error(request, 'Permission denied. Only auditors can upload documents directly.')
        return redirect('documents')
    
    engagement_id = request.POST.get('engagement_id')
    folder = request.POST.get('folder', 'workplan')
    files = request.FILES.getlist('files')
    
    if not engagement_id or not files:
        messages.error(request, 'Please select an engagement and at least one file.')
        return redirect('documents')
    
    try:
        engagement = get_object_or_404(Engagement, id=engagement_id)
        
        uploaded_count = 0
        for file_obj in files:
            # Create RequestDocument without a Request (direct upload)
            doc = RequestDocument.objects.create(
                engagement=engagement,
                file=file_obj,
                folder=folder,
                uploaded_by=request.user
            )
            # doc_type is auto-set in save() based on folder
            uploaded_count += 1
        
        if uploaded_count == 1:
            messages.success(request, 'Document uploaded successfully.')
        else:
            messages.success(request, f'{uploaded_count} documents uploaded successfully.')
        
        return redirect(f"{reverse('documents')}?engagement={engagement.id}&folder={folder}")
    except Exception as e:
        messages.error(request, f'Error uploading documents: {str(e)}')
        return redirect('documents')


 


def logout_view(request):
    """Log out the user and redirect to the login page."""
    logout(request)
    return redirect('/admin/login/')


@login_required
@require_http_methods(["POST"])
@role_required([ROLE_ADMIN, ROLE_CONTROL_ASSESSOR])
def generate_sheets(request, engagement_id):
    """
    Auto-generate Sheets (EngagementControls) for an engagement from the selected Standard.
    Rules (initial implementation):
    - Requires an engagement with a selected Standard
    - Pulls active StandardControls
    - Skips controls that already exist for the engagement
    - Marks generated controls with source='auto' and links to StandardControl
    """
    engagement = get_object_or_404(Engagement, id=engagement_id)
    if not engagement.standards.exists():
        messages.error(request, 'Please select at least one Standard for this engagement before generating sheets.')
        return redirect(f"{reverse('sheets')}?engagement={engagement.id}")
    
    created_count, skipped_count = generate_engagement_controls(engagement)
    
    if created_count == 0:
        messages.info(request, 'No new controls to generate. Sheets are already up to date.')
    else:
        standards_names = ', '.join([s.name for s in engagement.standards.all()])
        messages.success(request, f'Generated {created_count} controls from {standards_names}.')
    
    return redirect(f"{reverse('sheets')}?engagement={engagement.id}")


@login_required
@require_http_methods(["POST"])
def upload_evidence(request, request_id):
    """
    Upload multiple evidence documents for a request.
    Supports multi-file selection and appends to existing documents.
    Evidence uploads create RequestDocument records with doc_type='evidence'.
    When Client uploads, status changes from Open to In-Review.
    """
    try:
        req = get_object_or_404(Request, id=request_id)
        user_role = get_user_role(request.user)
        
        # Check permissions
        if not user_in_roles(request.user, [ROLE_ADMIN, ROLE_CONTROL_ASSESSOR, ROLE_CONTROL_REVIEWER, ROLE_CLIENT]):
            messages.error(request, 'Permission denied.')
            return redirect('requests_list')
        
        # Check if request is locked (Accepted requests cannot be modified by Clients)
        if req.is_locked and req.status == 'Accepted' and user_role == ROLE_CLIENT:
            messages.error(request, 'This request has been accepted and cannot be modified.')
            engagement_id = req.linked_control.engagement.id if req.linked_control.engagement else None
            if engagement_id:
                return redirect(f"{reverse('requests_list')}?engagement={engagement_id}")
            return redirect('requests_list')
        
        # Handle multiple file uploads
        files = request.FILES.getlist('evidence_files') or [request.FILES.get('evidence_file')]
        files = [f for f in files if f]  # Remove None values
        
        if not files:
            messages.error(request, 'Please select at least one file to upload.')
        else:
            uploaded_count = 0
            for file_obj in files:
                # Create RequestDocument record - this is what appears in Documents repository
                # Engagement is auto-set in save() from request.linked_control.engagement
                RequestDocument.objects.create(
                    request=req,
                    file=file_obj,
                    doc_type='evidence',
                    folder='workplan',  # Default folder for evidence
                    uploaded_by=request.user
                )
                uploaded_count += 1
            
            # Update request status if Client uploaded (Open -> In-Review)
            if req.status == 'Open' and user_role == ROLE_CLIENT:
                req.status = 'In-Review'
                req.save(update_fields=['status'])
            
            if uploaded_count == 1:
                messages.success(request, 'Evidence document uploaded successfully.')
            else:
                messages.success(request, f'{uploaded_count} evidence documents uploaded successfully.')
            
            # No status logic in Sheets per AuditSource behavior
        
        # Redirect back to Requests page
        engagement_id = req.linked_control.engagement.id if req.linked_control.engagement else None
        if engagement_id:
            return redirect(f"{reverse('requests_list')}?engagement={engagement_id}")
        return redirect('requests_list')
    except Exception as e:
        messages.error(request, f'Error uploading evidence: {str(e)}')
        return redirect('requests_list')


@login_required
@require_http_methods(["POST"])
def upload_workpaper(request, request_id):
    """
    Upload multiple workpaper documents for a request.
    Workpapers are uploaded by auditors (Admin, Assessor, Reviewer) from Sheets.
    Workpapers create RequestDocument records with doc_type='workpaper'.
    """
    try:
        req = get_object_or_404(Request, id=request_id)
        user_role = get_user_role(request.user)
        
        # Workpapers can only be uploaded by Admin, Assessor, Reviewer (NOT Clients)
        if not user_in_roles(request.user, [ROLE_ADMIN, ROLE_CONTROL_ASSESSOR, ROLE_CONTROL_REVIEWER]):
            messages.error(request, 'Only auditors can upload workpapers. Clients should use Requests to upload evidence.')
            return redirect('requests_list')
        
        # Handle multiple file uploads
        files = request.FILES.getlist('workpaper_files') or [request.FILES.get('workpaper_file')]
        files = [f for f in files if f]  # Remove None values
        
        if not files:
            messages.error(request, 'Please select at least one file to upload.')
        else:
            uploaded_count = 0
            for file_obj in files:
                # Create RequestDocument record - this appears in Documents repository
                # Engagement is auto-set in save() from request.linked_control.engagement
                RequestDocument.objects.create(
                    request=req,
                    file=file_obj,
                    doc_type='workpaper',
                    folder='workplan',  # Default folder for workpapers
                    uploaded_by=request.user
                )
                uploaded_count += 1
            
            # Update request status if needed
            if req.status == 'Open':
                req.status = 'In-Review'
                req.save(update_fields=['status'])
            
            if uploaded_count == 1:
                messages.success(request, 'Workpaper document uploaded successfully.')
            else:
                messages.success(request, f'{uploaded_count} workpaper documents uploaded successfully.')
        
        # Handle test notes separately (if provided)
        if 'auditor_test_notes' in request.POST:
            test_notes = request.POST.get('auditor_test_notes', '').strip()
            if test_notes:
                req.auditor_test_notes = test_notes
                if not req.prepared_by:
                    req.prepared_by = request.user
                req.save(update_fields=['auditor_test_notes', 'prepared_by'])
        
        # Redirect back to Sheets (workpapers are uploaded from Sheets)
        engagement_id = req.linked_control.engagement.id if req.linked_control.engagement else None
        if engagement_id:
            return redirect(f"{reverse('sheets')}?engagement={engagement_id}")
        return redirect('sheets')
    except Exception as e:
        messages.error(request, f'Error uploading workpaper: {str(e)}')
        return redirect('sheets')


@login_required
@require_http_methods(["POST"])
@role_required([ROLE_ADMIN, ROLE_CONTROL_ASSESSOR, ROLE_CONTROL_REVIEWER])
def review_request(request, request_id):
    """
    Handle Accept/Return actions for control requests.
    - Accept: Sets status to Accepted, locks request, records reviewer
    - Return: Sets status to Returned, unlocks request (allows Client to re-upload)
    Status transitions: Open → In-Review → Accepted/Returned
    """
    try:
        req = get_object_or_404(Request, id=request_id)
        user_role = get_user_role(request.user)
    
        # Check if request is locked (only Admin can override)
        if req.is_locked and req.status == 'Accepted' and user_role != ROLE_ADMIN:
            messages.error(request, 'This request has been accepted and is locked.')
            engagement_id = req.linked_control.engagement.id if req.linked_control.engagement else None
            if engagement_id:
                return redirect(f"{reverse('requests_list')}?engagement={engagement_id}")
            return redirect('requests_list')
        
        # Get status from POST data
        new_status = request.POST.get('status')
        if not new_status or new_status not in ['Accepted', 'Returned']:
            messages.error(request, 'Invalid status value.')
            engagement_id = req.linked_control.engagement.id if req.linked_control.engagement else None
            if engagement_id:
                return redirect(f"{reverse('requests_list')}?engagement={engagement_id}")
            return redirect('requests_list')
        
        # Validate acceptance requirements
        if new_status == 'Accepted':
            has_file = req.documents.filter(doc_type__in=['evidence', 'workpaper']).exists()
            has_notes = bool(req.auditor_test_notes and req.auditor_test_notes.strip())
            if not (has_file or has_notes):
                messages.error(
                    request, 
                    'Either a supporting file (evidence or workpaper) or non-empty Test Performed notes are required before acceptance.'
                )
                engagement_id = req.linked_control.engagement.id if req.linked_control.engagement else None
                if engagement_id:
                    return redirect(f"{reverse('requests_list')}?engagement={engagement_id}")
                return redirect('requests_list')
        
        # Update request status and lock state
        req.status = new_status
        if new_status == 'Accepted':
            req.reviewed_by = request.user
            req.reviewed_at = timezone.now()
            req.is_locked = True  # Lock when accepted - no further uploads
            messages.success(request, 'Request accepted and locked. Evidence is now read-only.')
        elif new_status == 'Returned':
            req.is_locked = False  # Unlock when returned - allows Client to re-upload
            req.status = 'Open'  # Reset to Open so Client can upload again
            messages.success(request, 'Request returned for revision. Client can re-upload evidence.')
        
        req.save()
        
        # Redirect back to Requests page
        engagement_id = req.linked_control.engagement.id if req.linked_control.engagement else None
        if engagement_id:
            return redirect(f"{reverse('requests_list')}?engagement={engagement_id}")
        return redirect('requests_list')
    except Exception as e:
        messages.error(request, f'Error reviewing request: {str(e)}')
        return redirect('requests_list')


@login_required
@require_http_methods(["POST"])
def unlock_request(request, request_id):
    """
    Unlock a control request. Only Admin, Control Assessor, and Control Reviewer can unlock.
    When unlocking:
    - Accepted status -> changes to In-Review
    - Returned status -> changes to In-Review
    - Other statuses -> remain unchanged
    """
    req = get_object_or_404(Request, id=request_id)
    user_role = get_user_role(request.user)
    
    if not user_in_roles(request.user, [ROLE_ADMIN, ROLE_CONTROL_ASSESSOR, ROLE_CONTROL_REVIEWER]):
        messages.error(request, 'Only administrators, control assessors, or control reviewers can unlock requests.')
        engagement_id = req.linked_control.engagement.id if req.linked_control.engagement else None
        if engagement_id:
            return redirect(f"{reverse('requests_list')}?engagement={engagement_id}")
        return redirect('requests_list')
    
    try:
        # Unlock the request
        req.is_locked = False
        
        # Restore status to In-Review if it was Accepted or Returned
        if req.status == 'Accepted' or req.status == 'Returned':
            req.status = 'In-Review'
        
        req.save()
        messages.success(request, 'Request unlocked.')
        
        engagement_id = req.linked_control.engagement.id if req.linked_control.engagement else None
        if engagement_id:
            return redirect(f"{reverse('requests_list')}?engagement={engagement_id}")
        return redirect('requests_list')
    except Exception as e:
        messages.error(request, f'Error unlocking request: {str(e)}')
        return redirect('requests_list')


@login_required
def download_file(request, file_type, request_id):
    req = get_object_or_404(Request, id=request_id)
    user_role = get_user_role(request.user)
    
    if not user_in_roles(request.user, [ROLE_ADMIN, ROLE_CONTROL_ASSESSOR, ROLE_CONTROL_REVIEWER, ROLE_CLIENT]):
        messages.error(request, 'Permission denied.')
        return redirect('dashboard')
    
    file_field = None
    if file_type == 'evidence':
        file_field = req.evidence_file
    elif file_type == 'workpaper':
        file_field = req.workpaper_file
    
    if file_field and file_field.name:
        try:
            response = FileResponse(file_field.open(), content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_field.name)}"'
            return response
        except Exception:
            messages.error(request, 'Error downloading file.')
            return redirect('dashboard')
    else:
        messages.error(request, 'File not found.')
        return redirect('dashboard')


@login_required
@require_http_methods(["POST"])
def delete_document(request, doc_id):
    """
    Delete a specific uploaded document.
    Allowed roles: Admin, Control Assessor, Control Reviewer.
    Cannot delete evidence files (those linked to Requests).
    """
    doc = get_object_or_404(RequestDocument, id=doc_id)

    if not user_in_roles(request.user, [ROLE_ADMIN, ROLE_CONTROL_ASSESSOR, ROLE_CONTROL_REVIEWER]):
        messages.error(request, 'Only administrators, control assessors, or control reviewers can delete documents.')
        return redirect('documents')

    # Cannot delete evidence files (from Requests)
    if doc.request and doc.doc_type == 'evidence':
        messages.error(request, 'Cannot delete evidence files. Evidence files are managed through Requests.')
        engagement_id = doc.engagement.id if doc.engagement else None
        if engagement_id:
            return redirect(f"{reverse('documents')}?engagement={engagement_id}")
        return redirect('documents')

    # Get engagement before deleting
    engagement_id = doc.engagement.id if doc.engagement else None
    folder = doc.folder

    # Delete file from storage then record
    try:
        doc.file.delete(save=False)
        doc.delete()
        messages.success(request, 'Document deleted successfully.')
    except Exception as e:
        messages.error(request, f'Error deleting document: {str(e)}')

    # No Sheets status logic per AuditSource behavior

    if engagement_id:
        return redirect(f"{reverse('documents')}?engagement={engagement_id}&folder={folder}")
    return redirect('documents')


@login_required
@require_http_methods(["POST"])
def delete_file(request, file_type, request_id):
    """
    Delete an uploaded evidence/workpaper file.
    Allowed roles: Admin, Control Assessor, Control Reviewer.
    """
    req = get_object_or_404(Request, id=request_id)

    if not user_in_roles(request.user, [ROLE_ADMIN, ROLE_CONTROL_ASSESSOR, ROLE_CONTROL_REVIEWER]):
        messages.error(request, 'Only administrators, control assessors, or control reviewers can delete documents.')
        return redirect('dashboard')

    file_field = None
    if file_type == 'evidence':
        file_field = req.evidence_file
    elif file_type == 'workpaper':
        file_field = req.workpaper_file

    if file_field and file_field.name:
        # Delete the file from storage and clear the field
        file_field.delete(save=False)
        if file_type == 'evidence':
            req.evidence_file = None
        else:
            req.workpaper_file = None
        req.save()
        messages.success(request, 'Document deleted successfully.')
    else:
        messages.error(request, 'No document found to delete.')

    engagement_id = req.linked_control.engagement.id if req.linked_control.engagement else None
    if engagement_id:
        return redirect(f"{reverse('sheets')}?engagement={engagement_id}")
    return redirect('sheets')


@login_required
def create_engagement(request):
    """
    Create engagement and auto-generate controls from selected standards.
    This is the primary entry point - controls are ALWAYS auto-generated.
    """
    user_role = get_user_role(request.user)
    if not user_in_roles(request.user, [ROLE_ADMIN, ROLE_CONTROL_ASSESSOR]):
        messages.error(request, 'Only administrators or control assessors can create engagements.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        client_name = request.POST.get('client_name', '')
        audit_year = request.POST.get('audit_year')
        standard_ids = request.POST.getlist('standards')  # Multiple standards allowed
        
        if not title or not standard_ids:
            messages.error(request, 'Title and at least one standard are required.')
            return render(request, 'audit/create_engagement.html', {
                'form': None,
                'standards': Standard.objects.all()
            })
        
        try:
            audit_year_int = int(audit_year) if audit_year else None
        except (ValueError, TypeError):
            audit_year_int = None
        
        try:
            engagement, created_count, skipped_count = create_engagement_with_controls(
                client_name=client_name,
                title=title,
                audit_year=audit_year_int,
                standard_ids=standard_ids,
                lead_auditor=request.user
            )
            messages.success(
                request, 
                f'Engagement created successfully. Generated {created_count} controls from standards.'
            )
            return redirect(f'{reverse("sheets")}?engagement={engagement.id}')
        except Exception as e:
            messages.error(request, f'Error creating engagement: {str(e)}')
    
    return render(request, 'audit/create_engagement.html', {
        'form': None,
        'standards': Standard.objects.all()
    })


@login_required
def create_control(request):
    """
    Manual control creation - RESTRICTED.
    Controls should be auto-generated from standards.
    This endpoint is only for rare custom controls.
    """
    user_role = get_user_role(request.user)
    if not user_in_roles(request.user, [ROLE_ADMIN, ROLE_CONTROL_ASSESSOR]):
        messages.error(request, 'Only administrators or control assessors can create controls.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        engagement_id = request.POST.get('engagement')
        control_id = request.POST.get('control_id')
        control_name = request.POST.get('control_name', '')
        control_description = request.POST.get('control_description', '')
        
        if not engagement_id or not control_id:
            messages.error(request, 'Engagement and Control ID are required.')
            return redirect('sheets')
        
        engagement = get_object_or_404(Engagement, id=engagement_id)
        
        # Check if control already exists
        if EngagementControl.objects.filter(engagement=engagement, control_id=control_id).exists():
            messages.error(request, f'Control {control_id} already exists for this engagement.')
            return redirect(f'{reverse("sheets")}?engagement={engagement_id}')
        
        # Create manual control
        control = EngagementControl.objects.create(
            engagement=engagement,
            control_id=control_id,
            control_name=control_name,
            control_description=control_description,
            source='manual',
                status='Open'
            )
        
        messages.success(request, f'Custom control {control_id} created successfully.')
        return redirect(f'{reverse("sheets")}?engagement={engagement_id}')
    
        engagement_id = request.GET.get('engagement')
    if not engagement_id:
        messages.error(request, 'Engagement is required.')
        return redirect('sheets')
    
    return render(request, 'audit/create_control.html', {
        'engagement_id': engagement_id,
        'engagement': get_object_or_404(Engagement, id=engagement_id)
    })
