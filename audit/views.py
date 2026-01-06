from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, FileResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.urls import reverse
from .models import Engagement, ControlRequirement, Request
from .forms import EvidenceUploadForm, WorkpaperUploadForm, RequestReviewForm, EngagementForm, ControlRequirementForm
import os


def get_user_role(user):
    """Determine user role based on groups or superuser status."""
    if user.is_superuser:
        return 'Admin'
    if user.groups.filter(name='Auditor').exists():
        return 'Auditor'
    if user.groups.filter(name='Contributor').exists():
        return 'Contributor'
    return 'Contributor'  # Default


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
    }
    
    return render(request, 'audit/dashboard.html', context)


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
    
    if user_role not in ['Contributor', 'Auditor', 'Admin']:
        messages.error(request, 'Permission denied.')
        return redirect('dashboard')
    
    form = EvidenceUploadForm(request.POST, request.FILES, instance=req)
    if form.is_valid():
        req = form.save(commit=False)
        if req.status == 'Open':
            req.status = 'In-Review'
        req.save()
        messages.success(request, 'Evidence uploaded successfully.')
    else:
        messages.error(request, 'Error uploading evidence.')
    
    engagement_id = req.linked_control.engagement.id if req.linked_control.engagement else None
    if engagement_id:
        return redirect(f"{reverse('dashboard')}?engagement={engagement_id}")
    return redirect('dashboard')


@login_required
@require_http_methods(["POST"])
def upload_workpaper(request, request_id):
    req = get_object_or_404(Request, id=request_id)
    user_role = get_user_role(request.user)
    
    if user_role not in ['Auditor', 'Admin']:
        messages.error(request, 'Only auditors can upload workpapers.')
        return redirect('dashboard')
    
    if req.is_locked:
        messages.error(request, 'This request is locked and cannot be modified.')
        return redirect('dashboard')
    
    form = WorkpaperUploadForm(request.POST, request.FILES, instance=req)
    if form.is_valid():
        req = form.save(commit=False)
        if not req.prepared_by:
            req.prepared_by = request.user
        req.save()
        messages.success(request, 'Workpaper and test notes saved successfully.')
    else:
        messages.error(request, 'Error uploading workpaper.')
        for error in form.errors.values():
            messages.error(request, error)
    
    engagement_id = req.linked_control.engagement.id if req.linked_control.engagement else None
    if engagement_id:
        return redirect(f"{reverse('dashboard')}?engagement={engagement_id}")
    return redirect('dashboard')


@login_required
@require_http_methods(["POST"])
def review_request(request, request_id):
    req = get_object_or_404(Request, id=request_id)
    user_role = get_user_role(request.user)
    
    if user_role not in ['Auditor', 'Admin']:
        messages.error(request, 'Only auditors can review requests.')
        return redirect('dashboard')
    
    if req.is_locked and user_role != 'Admin':
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
    
    if user_role != 'Admin':
        messages.error(request, 'Only administrators can unlock requests.')
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
    
    if user_role not in ['Auditor', 'Admin']:
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
def create_engagement(request):
    user_role = get_user_role(request.user)
    if user_role != 'Admin':
        messages.error(request, 'Only administrators can create engagements.')
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
    if user_role != 'Admin':
        messages.error(request, 'Only administrators can create controls.')
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
