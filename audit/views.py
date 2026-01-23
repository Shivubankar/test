from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, FileResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.urls import reverse
from django.db import transaction
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
    
    # Create a dict mapping control_id to list of requests (support multiple requests per control)
    from collections import defaultdict
    requests_dict = defaultdict(list)
    for req in requests:
        requests_dict[req.linked_control.id].append(req)
    
    is_admin_user = user_in_roles(request.user, [ROLE_ADMIN])
    # Create control-requests pairs for template
    control_requests = []
    for control in controls:
        control_requests_list = requests_dict.get(control.id, [])
        # Sort requests: Open first, then by creation date (newest first)
        # This ensures OPEN requests are prioritized for auto-selection
        sorted_requests = sorted(control_requests_list, key=lambda r: (r.status != 'OPEN', -r.id))
        # Get latest OPEN request for auto-selection, or first request
        latest_open_request = next((req for req in sorted_requests if req.status == 'OPEN'), None)
        primary_request = latest_open_request or (sorted_requests[0] if sorted_requests else None)
        
        # Filter workpapers only (not evidence) for Documents column
        workpaper_docs = RequestDocument.objects.filter(
            linked_control=control,
            doc_type='workpaper'
        ).select_related('standard', 'uploaded_by')
        
        can_undo_preparer = (control.preparer_signed_by == request.user) or is_admin_user
        can_undo_reviewer = (control.reviewer_signed_by == request.user) or is_admin_user
        control_requests.append({
            'control': control,
            'requests': sorted_requests,  # All requests sorted (Open first, then by creation date)
            'request': primary_request,  # Primary request (for backward compatibility)
            'request_count': len(control_requests_list),
            'workpaper_count': workpaper_docs.count(),  # Only workpapers, not evidence
            'workpaper_docs': workpaper_docs,  # Workpaper queryset for template
            'can_undo_preparer': can_undo_preparer and control.preparer_signed_at is not None,
            'can_undo_reviewer': can_undo_reviewer and control.reviewer_signed_at is not None,
        })
    
    engagements = Engagement.objects.all()
    user_role = get_user_role(request.user)
    is_control_assessor = request.user.groups.filter(name=ROLE_CONTROL_ASSESSOR).exists()
    is_control_reviewer = request.user.groups.filter(name=ROLE_CONTROL_REVIEWER).exists()
    is_client = request.user.groups.filter(name=ROLE_CLIENT).exists()
    
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
        
        # Calculate Row Sign-offs % (Completed requests)
        completed_requests = all_requests.filter(status='COMPLETED').count()
        row_signoffs_percent = (completed_requests / total_controls * 100) if total_controls > 0 else 0
        
        # Calculate Document Sign-offs % (Requests with documents)
        requests_with_docs = all_requests.filter(documents__isnull=False).distinct().count()
        doc_signoffs_percent = (requests_with_docs / total_controls * 100) if total_controls > 0 else 0
        
        # Calculate Requests Completion % (Non-Open requests)
        completed_requests_count = all_requests.exclude(status='OPEN').count()
        requests_completion_percent = (completed_requests_count / total_controls * 100) if total_controls > 0 else 0
        
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
@role_required([ROLE_ADMIN, ROLE_CONTROL_ASSESSOR, ROLE_CONTROL_REVIEWER, ROLE_CLIENT])
def upload_controls_from_excel(request):
    """
    Excel upload page for auto-generating EngagementControl rows.
    Hard guard: if any controls exist for engagement, do nothing.
    """
    engagement_id = request.GET.get('engagement')
    if request.method == 'POST':
        engagement_id = request.POST.get('engagement_id') or engagement_id

    engagement = get_object_or_404(Engagement, id=engagement_id) if engagement_id else None
    engagements = Engagement.objects.all()
    user_role = get_user_role(request.user)

    if request.method == 'POST':
        if not engagement:
            messages.error(request, 'Please select an engagement before uploading.')
            return redirect('excel_upload')

        file_obj = request.FILES.get('excel_file')
        if not file_obj:
            messages.error(request, 'Please select an Excel file to upload.')
            return redirect(f"{reverse('excel_upload')}?engagement={engagement.id}")

        filename = file_obj.name.lower()
        if not (filename.endswith('.xlsx') or filename.endswith('.xls')):
            messages.error(request, 'Invalid file type. Please upload an .xlsx or .xls file.')
            return redirect(f"{reverse('excel_upload')}?engagement={engagement.id}")

        # Hard guard: never generate if any controls already exist.
        if EngagementControl.objects.filter(engagement=engagement).exists():
            messages.warning(request, 'Controls already exist for this engagement. Excel upload skipped.')
            return redirect(f"{reverse('excel_upload')}?engagement={engagement.id}")

        try:
            import pandas as pd
        except ImportError:
            messages.error(request, 'Excel upload requires pandas. Please install pandas and try again.')
            return redirect(f"{reverse('excel_upload')}?engagement={engagement.id}")

        try:
            df = pd.read_excel(file_obj)
        except Exception as e:
            messages.error(request, f'Unable to read Excel file: {str(e)}')
            return redirect(f"{reverse('excel_upload')}?engagement={engagement.id}")

        def normalize_column_name(value):
            name = str(value).strip().lower()
            name = name.replace(' ', '_')
            name = ''.join(ch for ch in name if ch.isalnum() or ch == '_')
            return name

        normalized_columns = {normalize_column_name(c): c for c in df.columns}
        aliases = {
            'control_id': {'control_id', 'control id'},
            'control_description': {'control_description', 'control description'},
        }

        rename_map = {}
        for canonical, names in aliases.items():
            for name in names:
                normalized = normalize_column_name(name)
                if normalized in normalized_columns:
                    rename_map[normalized_columns[normalized]] = canonical
                    break

        required_columns = ['control_id', 'control_description']
        missing_columns = [c for c in required_columns if c not in rename_map.values()]
        if missing_columns:
            messages.error(
                request,
                "Required columns not found. Accepted names: Control ID, Control Description (case-insensitive)"
            )
            return redirect(f"{reverse('excel_upload')}?engagement={engagement.id}")

        df = df.rename(columns=rename_map)

        rows = []
        row_errors = []
        duplicates = set()
        seen = set()
        for idx, row in df.iterrows():
            control_id = row.get('control_id')
            control_description = row.get('control_description')

            if control_id is None or pd.isna(control_id):
                control_id = ''
            else:
                control_id = str(control_id).strip()

            if control_description is None or pd.isna(control_description):
                control_description = ''
            else:
                control_description = str(control_description).strip()

            if not control_id or not control_description:
                row_errors.append(idx + 2)
                continue

            normalized_id = control_id.lower()
            if normalized_id in seen:
                duplicates.add(control_id)
            else:
                seen.add(normalized_id)
                rows.append({
                    'control_id': control_id,
                    'control_description': control_description,
                })

        if row_errors:
            messages.error(
                request,
                f"Missing required values in rows: {', '.join(str(r) for r in row_errors)}"
            )
            return redirect(f"{reverse('excel_upload')}?engagement={engagement.id}")

        if duplicates:
            messages.error(
                request,
                f"Duplicate control_id values detected: {', '.join(sorted(duplicates))}"
            )
            return redirect(f"{reverse('excel_upload')}?engagement={engagement.id}")

        if not rows:
            messages.error(request, 'No valid control rows found in the Excel file.')
            return redirect(f"{reverse('excel_upload')}?engagement={engagement.id}")

        try:
            with transaction.atomic():
                for row in rows:
                    EngagementControl.objects.create(
                        engagement=engagement,
                        control_id=row['control_id'],
                        control_name=row['control_id'],
                        control_description=row['control_description'],
                        source='excel',
                        test_applied='',
                        test_performed='',
                        test_results='',
                    )
        except Exception as e:
            messages.error(request, f'Error creating controls: {str(e)}')
            return redirect(f"{reverse('excel_upload')}?engagement={engagement.id}")

        messages.success(request, f'Created {len(rows)} controls from Excel upload.')
        return redirect(f"{reverse('sheets')}?engagement={engagement.id}")

    context = {
        'engagement': engagement,
        'engagements': engagements,
        'user_role': user_role,
    }
    return render(request, 'audit/excel_upload.html', context)

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
    Supports both regular form submission and AJAX requests.
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

    # Check if this is an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'Control {control.control_id} saved'
        })

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
        # Get standard from control
        standard = None
        if control.standard_control:
            standard = control.standard_control.standard
        RequestDocument.objects.create(
            engagement=control.engagement,
            linked_control=control,
            standard=standard,
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
@require_http_methods(["POST"])
def undo_signoff_control(request, control_id):
    """
    Undo a sign-off on a control by role (preparer or reviewer).
    Clears signed_by and signed_at fields only.
    role param: preparer | reviewer
    """
    control = get_object_or_404(EngagementControl, id=control_id)
    role = request.POST.get('role')
    is_admin_user = user_in_roles(request.user, [ROLE_ADMIN])

    if role == 'preparer':
        if not (is_admin_user or control.preparer_signed_by == request.user):
            messages.error(request, 'You do not have permission to undo Preparer sign-off.')
            return redirect(f"{reverse('sheets')}?engagement={control.engagement.id}")
        control.preparer_signed_by = None
        control.preparer_signed_at = None
        control.save(update_fields=['preparer_signed_by', 'preparer_signed_at'])
        messages.success(request, 'Preparer sign-off undone.')
    elif role == 'reviewer':
        if not (is_admin_user or control.reviewer_signed_by == request.user):
            messages.error(request, 'You do not have permission to undo Reviewer sign-off.')
            return redirect(f"{reverse('sheets')}?engagement={control.engagement.id}")
        control.reviewer_signed_by = None
        control.reviewer_signed_at = None
        control.save(update_fields=['reviewer_signed_by', 'reviewer_signed_at'])
        messages.success(request, 'Reviewer sign-off undone.')
    else:
        messages.error(request, 'Invalid sign-off role.')

    return redirect(f"{reverse('sheets')}?engagement={control.engagement.id}")


@login_required
def request_detail(request, pk):
    """
    Request detail page showing request information and evidence upload functionality.
    """
    req = get_object_or_404(Request, pk=pk)
    user_role = get_user_role(request.user)
    
    # Get all evidence documents for this request
    evidence_docs = RequestDocument.objects.filter(
        request=req,
        doc_type='evidence'
    ).select_related('standard', 'uploaded_by', 'linked_control').order_by('-uploaded_at')
    
    # Sign-off permissions
    is_admin_user = request.user.is_superuser
    is_control_assessor = request.user.groups.filter(name=ROLE_CONTROL_ASSESSOR).exists()
    is_control_reviewer = request.user.groups.filter(name=ROLE_CONTROL_REVIEWER).exists()
    
    # Check if user can undo their own sign-offs
    can_undo_preparer = (req.prepared_by == request.user) or is_admin_user
    can_undo_reviewer = (req.reviewed_by == request.user) or is_admin_user
    
    context = {
        'request_obj': req,
        'evidence_docs': evidence_docs,
        'user_role': user_role,
        'can_sign_preparer': (is_admin_user or is_control_assessor) and not req.preparer_signed,
        'can_sign_reviewer': (is_admin_user or is_control_reviewer) and not req.reviewer_signed,
        'can_undo_preparer': can_undo_preparer and req.preparer_signed,
        'can_undo_reviewer': can_undo_reviewer and req.reviewer_signed,
    }
    
    return render(request, 'audit/request_detail.html', context)


@login_required
def requests_list(request):
    """
    Central evidence request tracker.
    Shows requests with Key, Status, Title, Description, Due date, Owner, Tags.
    Status lifecycle: Open, Ready for Review, Completed.
    Includes status counts and search by title/description/tags.
    Supports filtering by engagement and standard.
    """
    engagement_id = request.GET.get('engagement')
    standard_id = request.GET.get('standard')
    status_filter = request.GET.get('status')
    q = request.GET.get('q', '').strip()
    
    # Get base queryset of controls
    if engagement_id:
        engagement = get_object_or_404(Engagement, id=engagement_id)
        controls = EngagementControl.objects.filter(engagement=engagement)
        
        # Filter by standard if provided
        if standard_id:
            controls = controls.filter(standard_control__standard_id=standard_id)
    else:
        engagement = Engagement.objects.first()
        if engagement:
            controls = EngagementControl.objects.filter(engagement=engagement)
            if standard_id:
                controls = controls.filter(standard_control__standard_id=standard_id)
        else:
            controls = EngagementControl.objects.none()
    
    # Get all requests for these controls
    all_requests = Request.objects.filter(linked_control__in=controls).select_related(
        'linked_control', 'linked_control__standard_control__standard', 'assignee', 'prepared_by', 'reviewed_by'
    )
    
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
    
    # Counts for chips - computed from database queries
    base_requests = Request.objects.filter(linked_control__in=controls)
    counts = {
        'All': base_requests.count(),
        'OPEN': base_requests.filter(status='OPEN').count(),
        'READY_FOR_REVIEW': base_requests.filter(status='READY_FOR_REVIEW').count(),
        'COMPLETED': base_requests.filter(status='COMPLETED').count(),
    }
    
    # Prefetch document counts for each request
    from django.db.models import Count, Q
    all_requests = all_requests.annotate(
        evidence_count=Count('documents', filter=Q(documents__doc_type='evidence')),
        workpaper_count=Count('documents', filter=Q(documents__doc_type='workpaper'))
    )
    
    # Get engagements with their standards for dropdown
    engagements = Engagement.objects.prefetch_related('standards').all()
    user_role = get_user_role(request.user)
    
    # Get selected standard if provided
    selected_standard = None
    if standard_id:
        try:
            from .models import Standard
            selected_standard = Standard.objects.get(id=standard_id)
        except Standard.DoesNotExist:
            pass
    
    context = {
        'engagement': engagement,
        'engagements': engagements,
        'selected_standard': selected_standard,
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
                status='OPEN',
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
    Central document repository with filter-based structure.
    Shows documents organized by Engagement → Standard → Control.
    Documents module is VIEW ONLY - no uploads here.
    """
    engagement_id = request.GET.get('engagement')
    standard_id = request.GET.get('standard')
    control_id = request.GET.get('control')
    
    user_role = get_user_role(request.user)
    
    # Documents module is view-only
    can_delete = user_in_roles(request.user, [ROLE_ADMIN, ROLE_CONTROL_ASSESSOR, ROLE_CONTROL_REVIEWER])
    
    # Engagement is required
    if engagement_id:
        engagement = get_object_or_404(Engagement, id=engagement_id)
    else:
        engagement = Engagement.objects.first()
        if engagement:
            # Redirect to include engagement in URL
            return redirect(f"{reverse('documents')}?engagement={engagement.id}")
    
    # Get all documents for the engagement
    if engagement:
        documents = RequestDocument.objects.filter(engagement=engagement).select_related(
            'request', 'request__linked_control', 'linked_control', 'linked_control__standard_control__standard',
            'standard', 'uploaded_by', 'engagement'
        )
        
        # Filter by standard if provided
        if standard_id:
            documents = documents.filter(standard_id=standard_id)
        
        # Filter by control if provided
        if control_id:
            documents = documents.filter(linked_control_id=control_id)
        
        # Order by updated date (newest first)
        documents = documents.order_by('-updated_at')
    else:
        documents = RequestDocument.objects.none()
    
    # Get standards and controls for the filter tree
    standards_list = []
    selected_standard = None
    selected_control = None
    
    if engagement:
        # Get all standards for this engagement
        standards = engagement.standards.all().order_by('name')
        
        # Get selected standard
        if standard_id:
            try:
                selected_standard = Standard.objects.get(id=standard_id)
            except Standard.DoesNotExist:
                pass
        
        # Get selected control
        if control_id:
            try:
                selected_control = EngagementControl.objects.get(id=control_id, engagement=engagement)
            except EngagementControl.DoesNotExist:
                pass
        
        # Build standards list with controls
        for standard in standards:
            controls = EngagementControl.objects.filter(
                engagement=engagement,
                standard_control__standard=standard
            ).select_related('standard_control').order_by('control_id')
            
            # Count documents per control
            for control in controls:
                control.doc_count = documents.filter(linked_control=control).count()
            
            standards_list.append({
                'standard': standard,
                'controls': controls,
                'total_docs': sum(c.doc_count for c in controls)
            })
    
    engagements = Engagement.objects.all()
    
    context = {
        'engagement': engagement,
        'engagements': engagements,
        'user_role': user_role,
        'documents': documents,
        'standards_list': standards_list,
        'selected_standard': selected_standard,
        'selected_control': selected_control,
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
            return redirect('request_detail', pk=req.id)
        
        # Check if request is locked (Accepted requests cannot be modified by Clients)
        if req.is_locked and req.status == 'COMPLETED' and user_role == ROLE_CLIENT:
            messages.error(request, 'This request has been accepted and cannot be modified.')
            return redirect('request_detail', pk=req.id)
        
        # Handle multiple file uploads
        files = request.FILES.getlist('evidence_files') or [request.FILES.get('evidence_file')]
        files = [f for f in files if f]  # Remove None values
        
        if not files:
            messages.error(request, 'Please select at least one file to upload.')
        else:
            uploaded_count = 0
            for file_obj in files:
                # Create RequestDocument record - this is what appears in Documents repository
                # Explicitly set required relationships to avoid relying on save().
                RequestDocument.objects.create(
                    request=req,
                    engagement=req.linked_control.engagement,
                    linked_control=req.linked_control,
                    standard=(
                        req.linked_control.standard_control.standard
                        if req.linked_control.standard_control else None
                    ),
                    file=file_obj,
                    doc_type='evidence',
                    folder='workplan',  # Default folder for evidence
                    uploaded_by=request.user
                )
                uploaded_count += 1
            
            # Recalculate request status automatically based on evidence and sign-offs
            req.recalculate_status()
            req.save()
            
            if uploaded_count == 1:
                messages.success(request, 'Evidence document uploaded successfully.')
            else:
                messages.success(request, f'{uploaded_count} evidence documents uploaded successfully.')
        
        # Redirect back to Request Detail page
        return redirect('request_detail', pk=req.id)
    except Exception as e:
        messages.error(request, f'Error uploading evidence: {str(e)}')
        if 'req' in locals():
            return redirect('request_detail', pk=req.id)
        return redirect('requests_list')


@login_required
@require_http_methods(["POST"])
def upload_evidence_from_sheets(request, control_id):
    """
    Upload evidence documents directly from Sheets (Workplan) module.
    Simple, minimal upload flow - no dropdowns, no reuse logic.
    Auto-selects latest OPEN request or creates new request if none exists.
    Redirects back to Sheets (not Requests page).
    """
    try:
        control = get_object_or_404(EngagementControl, id=control_id)
        user_role = get_user_role(request.user)
        
        # Check permissions
        if not user_in_roles(request.user, [ROLE_ADMIN, ROLE_CONTROL_ASSESSOR, ROLE_CONTROL_REVIEWER, ROLE_CLIENT]):
            messages.error(request, 'Permission denied.')
            return redirect(f"{reverse('sheets')}?engagement={control.engagement.id}")
        
        # Get or create request
        request_id = request.POST.get('request_id')
        
        if request_id:
            req = get_object_or_404(Request, id=request_id, linked_control=control)
        else:
            # Auto-create request if none exists
            # Find latest OPEN request for this control
            existing_requests = Request.objects.filter(linked_control=control).order_by('-created_at')
            latest_open_request = existing_requests.filter(status='OPEN').first()
            
            if latest_open_request:
                req = latest_open_request
            else:
                # Create new request
                req = Request.objects.create(
                    linked_control=control,
                    title=f"Evidence Request - {control.control_id}",
                    status='OPEN',
                    assignee=control.engagement.lead_auditor if control.engagement.lead_auditor else request.user
                )
        
        # Check if request is locked (Accepted requests cannot be modified by Clients)
        if req.is_locked and req.status == 'COMPLETED' and user_role == ROLE_CLIENT:
            messages.error(request, 'This request has been accepted and cannot be modified.')
            return redirect(f"{reverse('sheets')}?engagement={control.engagement.id}")
        
        # Handle file uploads
        files = request.FILES.getlist('evidence_files')
        files = [f for f in files if f]  # Remove None values
        
        if not files:
            messages.error(request, 'Please select at least one file to upload.')
        else:
            uploaded_count = 0
            for file_obj in files:
                # Get standard from control
                standard = None
                if control.standard_control:
                    standard = control.standard_control.standard
                # Create RequestDocument record with default 'evidence' folder
                RequestDocument.objects.create(
                    request=req,
                    engagement=control.engagement,
                    linked_control=control,
                    standard=standard,
                    file=file_obj,
                    doc_type='evidence',
                    folder='evidence',  # Default folder
                    uploaded_by=request.user
                )
                uploaded_count += 1
            
            # Recalculate request status automatically based on evidence and sign-offs
            req.recalculate_status()
            req.save()
            
            if uploaded_count == 1:
                messages.success(request, 'Evidence file uploaded successfully.')
            else:
                messages.success(request, f'{uploaded_count} evidence files uploaded successfully.')
        
        # Redirect back to Sheets (NOT Requests page)
        return redirect(f"{reverse('sheets')}?engagement={control.engagement.id}")
    except Exception as e:
        messages.error(request, f'Error uploading evidence: {str(e)}')
        if 'control' in locals():
            return redirect(f"{reverse('sheets')}?engagement={control.engagement.id}")
        return redirect('sheets')


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
            # Status will be recalculated automatically in save()
            
            if uploaded_count == 1:
                messages.success(request, 'Workpaper document uploaded successfully.')
            else:
                messages.success(request, f'{uploaded_count} workpaper documents uploaded successfully.')
        
        # Handle test notes separately (if provided)
        if 'auditor_test_notes' in request.POST:
            test_notes = request.POST.get('auditor_test_notes', '').strip()
            if test_notes:
                req.auditor_test_notes = test_notes
        # Note: Setting prepared_by here doesn't automatically sign off
        # Sign-off must be done explicitly via signoff_request view
        # Status will be recalculated automatically in save()
        req.save()
        
        # Redirect back to Sheets (workpapers are uploaded from Sheets)
        engagement_id = req.linked_control.engagement.id if req.linked_control and req.linked_control.engagement else None
        if engagement_id:
            return redirect(f"{reverse('sheets')}?engagement={engagement_id}")
        return redirect('sheets')
    except Exception as e:
        messages.error(request, f'Error uploading workpaper: {str(e)}')
        return redirect('sheets')


@login_required
@require_http_methods(["POST"])
def signoff_request(request, request_id):
    """
    Record a sign-off on a request by role (preparer or reviewer).
    Sets boolean flags and timestamps. Status is automatically recalculated.
    role param: preparer | reviewer
    """
    from django.utils import timezone
    req = get_object_or_404(Request, id=request_id)
    role = request.POST.get('role')
    now = timezone.now()
    
    if role == 'preparer':
        # Permission check: Admin or Control Assessor can sign as Preparer
        if not user_in_roles(request.user, [ROLE_ADMIN, ROLE_CONTROL_ASSESSOR]):
            messages.error(request, 'You do not have permission to sign as Preparer.')
            return redirect('request_detail', pk=req.id)
        # Set preparer sign-off
        req.preparer_signed = True
        req.prepared_by = request.user
        req.preparer_signed_at = now
        messages.success(request, 'Preparer sign-off recorded.')
    elif role == 'reviewer':
        # Permission check: Admin or Control Reviewer can sign as Reviewer
        if not user_in_roles(request.user, [ROLE_ADMIN, ROLE_CONTROL_REVIEWER]):
            messages.error(request, 'You do not have permission to sign as Reviewer.')
            return redirect('request_detail', pk=req.id)
        # Set reviewer sign-off
        req.reviewer_signed = True
        req.reviewed_by = request.user
        req.reviewed_at = now
        messages.success(request, 'Reviewer sign-off recorded.')
    else:
        messages.error(request, 'Invalid sign-off role.')
        return redirect('request_detail', pk=req.id)
    
    # Save sign-off fields first
    if role == 'preparer':
        req.save(update_fields=['preparer_signed', 'prepared_by', 'preparer_signed_at'])
    else:
        req.save(update_fields=['reviewer_signed', 'reviewed_by', 'reviewed_at'])
    
    # Recalculate status automatically based on sign-off flags
    req.recalculate_status()
    
    return redirect('request_detail', pk=req.id)


@login_required
@require_http_methods(["POST"])
def undo_signoff_request(request, request_id):
    """
    Undo a sign-off on a request by role (preparer or reviewer).
    Clears boolean flags and timestamps. Status is automatically recalculated.
    role param: preparer | reviewer
    """
    req = get_object_or_404(Request, id=request_id)
    role = request.POST.get('role')
    
    if role == 'preparer':
        # Permission check: Only the user who signed can undo, or Admin
        if not (req.prepared_by == request.user or user_in_roles(request.user, [ROLE_ADMIN])):
            messages.error(request, 'You do not have permission to undo Preparer sign-off.')
            return redirect('request_detail', pk=req.id)
        # Clear preparer sign-off
        req.preparer_signed = False
        req.prepared_by = None
        req.preparer_signed_at = None
        messages.success(request, 'Preparer sign-off undone.')
    elif role == 'reviewer':
        # Permission check: Only the user who signed can undo, or Admin
        if not (req.reviewed_by == request.user or user_in_roles(request.user, [ROLE_ADMIN])):
            messages.error(request, 'You do not have permission to undo Reviewer sign-off.')
            return redirect('request_detail', pk=req.id)
        # Clear reviewer sign-off
        req.reviewer_signed = False
        req.reviewed_by = None
        req.reviewed_at = None
        messages.success(request, 'Reviewer sign-off undone.')
    else:
        messages.error(request, 'Invalid sign-off role.')
        return redirect('request_detail', pk=req.id)
    
    # Save cleared sign-off fields first
    if role == 'preparer':
        req.save(update_fields=['preparer_signed', 'prepared_by', 'preparer_signed_at'])
    else:
        req.save(update_fields=['reviewer_signed', 'reviewed_by', 'reviewed_at'])
    
    # Recalculate status automatically based on sign-off flags
    req.recalculate_status()
    
    return redirect('request_detail', pk=req.id)


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
        
        # Status will be recalculated automatically in save() based on sign-off flags
        req.save()
        messages.success(request, 'Request unlocked.')
        
        # Redirect back to Request Detail page
        return redirect('request_detail', pk=req.id)
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

    # Cannot delete evidence files (from Requests) - but allow deletion from request_detail if not read-only
    if doc.request and doc.doc_type == 'evidence' and doc.is_read_only:
        messages.error(request, 'Cannot delete read-only evidence files.')
        if doc.request:
            return redirect('request_detail', pk=doc.request.id)
        engagement_id = doc.engagement.id if doc.engagement else None
        if engagement_id:
            return redirect(f"{reverse('documents')}?engagement={engagement_id}")
        return redirect('documents')

    # Get engagement and request before deleting
    engagement_id = doc.engagement.id if doc.engagement else None
    folder = doc.folder
    request_id = doc.request.id if doc.request else None

    # Delete file from storage then record
    try:
        doc.file.delete(save=False)
        doc.delete()
        messages.success(request, 'Document deleted successfully.')
        
        # Recalculate request status if document was linked to a request
        if request_id:
            req = Request.objects.get(id=request_id)
            req.recalculate_status()
            req.save()
    except Exception as e:
        messages.error(request, f'Error deleting document: {str(e)}')

    # Redirect back to request_detail if deleting from a request
    if request_id:
        return redirect('request_detail', pk=request_id)
    
    # Otherwise redirect to documents
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
