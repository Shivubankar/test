from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, FileResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.urls import reverse
from .models import Engagement, ControlRequirement, Request, RequestDocument
from .forms import EvidenceUploadForm, WorkpaperUploadForm, RequestReviewForm, EngagementForm, ControlRequirementForm
import os
from functools import wraps


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
def dashboard(request):
    engagement_id = request.GET.get('engagement')
    year = request.GET.get('year')
    
    if engagement_id:
        engagement = get_object_or_404(Engagement, id=engagement_id)
        controls = ControlRequirement.objects.filter(engagement=engagement).select_related('engagement')
        
        # Filter by year if provided
        if year:
            try:
                year_int = int(year)
                controls = controls.filter(year=year_int)
            except (ValueError, TypeError):
                pass  # Invalid year, ignore filter
    else:
        engagement = Engagement.objects.first()
        if engagement:
            controls = ControlRequirement.objects.filter(engagement=engagement).select_related('engagement')
            # Filter by year if provided
            if year:
                try:
                    year_int = int(year)
                    controls = controls.filter(year=year_int)
                except (ValueError, TypeError):
                    pass  # Invalid year, ignore filter
        else:
            controls = ControlRequirement.objects.none()
    
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
    
    # Get available years for the selected engagement
    available_years = []
    if engagement:
        available_years = list(
            ControlRequirement.objects
            .filter(engagement=engagement)
            .exclude(year__isnull=True)
            .values_list('year', flat=True)
            .distinct()
            .order_by('-year')
        )
    
    # Convert selected_year to int for template comparison
    selected_year_int = None
    if year:
        try:
            selected_year_int = int(year)
        except (ValueError, TypeError):
            pass
    
    context = {
        'engagement': engagement,
        'engagements': engagements,
        'control_requests': control_requests,
        'user_role': user_role,
        'selected_year': selected_year_int,
        'available_years': available_years,
        'can_upload_evidence': is_admin_user or is_control_assessor or is_control_reviewer or is_client,
        'can_upload_workpaper': is_admin_user or is_control_assessor or is_control_reviewer,
        'can_signoff': is_admin_user or is_control_assessor or is_control_reviewer,
    }
    
    return render(request, 'audit/dashboard.html', context)


def logout_view(request):
    """Log out the user and redirect to the login page."""
    logout(request)
    return redirect('/admin/login/')


@login_required
def get_years(request):
    """AJAX endpoint to get available years for an engagement"""
    engagement_id = request.GET.get('engagement')
    
    if not engagement_id:
        return JsonResponse({'years': []})
    
    try:
        engagement = get_object_or_404(Engagement, id=engagement_id)
        years = list(
            ControlRequirement.objects
            .filter(engagement=engagement)
            .exclude(year__isnull=True)
            .values_list('year', flat=True)
            .distinct()
            .order_by('-year')
        )
        return JsonResponse({'years': years})
    except Exception as e:
        return JsonResponse({'years': []})


@login_required
@require_http_methods(["POST"])
def upload_evidence(request, request_id):
    req = get_object_or_404(Request, id=request_id)
    user_role = get_user_role(request.user)
    
    if not user_in_roles(request.user, [ROLE_ADMIN, ROLE_CONTROL_ASSESSOR, ROLE_CONTROL_REVIEWER, ROLE_CLIENT]):
        messages.error(request, 'Permission denied.')
        return redirect('dashboard')
    
    file_obj = request.FILES.get('evidence_file')
    if not file_obj:
        messages.error(request, 'Please select a file to upload.')
    else:
        RequestDocument.objects.create(
            request=req,
            file=file_obj,
            doc_type='evidence',
            uploaded_by=request.user
        )
        if req.status == 'Open':
            req.status = 'In-Review'
            req.save(update_fields=['status'])
        messages.success(request, 'Evidence uploaded successfully.')
    
    engagement_id = req.linked_control.engagement.id if req.linked_control.engagement else None
    if engagement_id:
        return redirect(f"{reverse('dashboard')}?engagement={engagement_id}")
    return redirect('dashboard')


@login_required
@require_http_methods(["POST"])
def upload_workpaper(request, request_id):
    req = get_object_or_404(Request, id=request_id)
    user_role = get_user_role(request.user)
    
    if not user_in_roles(request.user, [ROLE_ADMIN, ROLE_CONTROL_ASSESSOR, ROLE_CONTROL_REVIEWER, ROLE_CLIENT]):
        messages.error(request, 'Only permitted roles can upload workpapers.')
        return redirect('dashboard')
    
    if req.is_locked:
        messages.error(request, 'This request is locked and cannot be modified.')
        return redirect('dashboard')
    
    file_obj = request.FILES.get('workpaper_file')
    form = WorkpaperUploadForm(request.POST, instance=req)
    if form.is_valid():
        req = form.save(commit=False)
        created_doc = False
        if file_obj:
            RequestDocument.objects.create(
                request=req,
                file=file_obj,
                doc_type='workpaper',
                uploaded_by=request.user
            )
            created_doc = True
        if not req.prepared_by:
            req.prepared_by = request.user
        req.save()
        if created_doc:
            messages.success(request, 'Workpaper uploaded and notes saved.')
        else:
            messages.success(request, 'Notes saved.')
    else:
        messages.error(request, 'Error saving workpaper/notes.')
        for error in form.errors.values():
            messages.error(request, error)
    
    engagement_id = req.linked_control.engagement.id if req.linked_control.engagement else None
    if engagement_id:
        return redirect(f"{reverse('dashboard')}?engagement={engagement_id}")
    return redirect('dashboard')


@login_required
@require_http_methods(["POST"])
@role_required([ROLE_ADMIN, ROLE_CONTROL_ASSESSOR, ROLE_CONTROL_REVIEWER])
def review_request(request, request_id):
    req = get_object_or_404(Request, id=request_id)
    user_role = get_user_role(request.user)
    
    if req.is_locked and user_role != ROLE_ADMIN:
        messages.error(request, 'This request is locked.')
        return redirect('dashboard')
    
    form = RequestReviewForm(request.POST, instance=req)
    if form.is_valid():
        req = form.save(commit=False)
        if req.status == 'Accepted':
            req.reviewed_by = request.user
            req.reviewed_at = timezone.now()
        req.save()
        
        if req.status == 'Accepted':
            messages.success(request, 'Request accepted and locked.')
        elif req.status == 'Returned':
            messages.success(request, 'Request returned for revision.')
        else:
            messages.success(request, 'Request status updated.')
    else:
        messages.error(request, 'Error updating request status.')
        for error in form.errors.values():
            messages.error(request, error)
    
    engagement_id = req.linked_control.engagement.id if req.linked_control.engagement else None
    if engagement_id:
        return redirect(f"{reverse('dashboard')}?engagement={engagement_id}")
    return redirect('dashboard')


@login_required
@require_http_methods(["POST"])
def unlock_request(request, request_id):
    req = get_object_or_404(Request, id=request_id)
    user_role = get_user_role(request.user)
    
    if not user_in_roles(request.user, [ROLE_ADMIN, ROLE_CONTROL_ASSESSOR, ROLE_CONTROL_REVIEWER]):
        messages.error(request, 'Only administrators, control assessors, or control reviewers can unlock requests.')
        return redirect('dashboard')
    
    req.is_locked = False
    if req.status == 'Accepted':
        req.status = 'In-Review'
    req.save()
    messages.success(request, 'Request unlocked.')
    
    engagement_id = req.linked_control.engagement.id if req.linked_control.engagement else None
    if engagement_id:
        return redirect(f"{reverse('dashboard')}?engagement={engagement_id}")
    return redirect('dashboard')


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
    """
    doc = get_object_or_404(RequestDocument, id=doc_id)
    req = doc.request

    if not user_in_roles(request.user, [ROLE_ADMIN, ROLE_CONTROL_ASSESSOR, ROLE_CONTROL_REVIEWER]):
        messages.error(request, 'Only administrators, control assessors, or control reviewers can delete documents.')
        return redirect('dashboard')

    # Delete file from storage then record
    doc.file.delete(save=False)
    doc.delete()
    messages.success(request, 'Document deleted successfully.')

    engagement_id = req.linked_control.engagement.id if req.linked_control.engagement else None
    if engagement_id:
        return redirect(f"{reverse('dashboard')}?engagement={engagement_id}")
    return redirect('dashboard')


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
        return redirect(f"{reverse('dashboard')}?engagement={engagement_id}")
    return redirect('dashboard')


@login_required
def create_engagement(request):
    user_role = get_user_role(request.user)
    if not user_in_roles(request.user, [ROLE_ADMIN, ROLE_CONTROL_ASSESSOR]):
        messages.error(request, 'Only administrators or control assessors can create engagements.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = EngagementForm(request.POST)
        if form.is_valid():
            engagement = form.save()
            messages.success(request, 'Engagement created successfully.')
            return redirect(f'/?engagement={engagement.id}')
    else:
        form = EngagementForm()
    
    return render(request, 'audit/create_engagement.html', {'form': form})


@login_required
def create_control(request):
    user_role = get_user_role(request.user)
    if not user_in_roles(request.user, [ROLE_ADMIN, ROLE_CONTROL_ASSESSOR]):
        messages.error(request, 'Only administrators or control assessors can create controls.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ControlRequirementForm(request.POST)
        if form.is_valid():
            control = form.save()
            # Create a request for this control
            Request.objects.create(
                linked_control=control,
                assignee=control.engagement.lead_auditor,
                status='Open'
            )
            messages.success(request, 'Control created successfully.')
            engagement_id = control.engagement.id
            return redirect(f'/?engagement={engagement_id}')
    else:
        engagement_id = request.GET.get('engagement')
        form = ControlRequirementForm(initial={'engagement': engagement_id} if engagement_id else {})
    
    return render(request, 'audit/create_control.html', {'form': form})
