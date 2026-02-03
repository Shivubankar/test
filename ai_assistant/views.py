from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from audit.ollama_service import generate_ai_response


@login_required
@require_http_methods(["GET"])
def ai_assistant(request):
    return render(request, 'ai_assistant/chat.html')


@login_required
@require_http_methods(["POST"])
def send_message(request):
    message = request.POST.get('message', '').strip()
    if not message:
        return JsonResponse({'success': False, 'error': 'Message is empty.'}, status=400)

    try:
        reply = generate_ai_response(message)
    except Exception as exc:
        return JsonResponse({'success': False, 'error': str(exc)}, status=503)

    return JsonResponse({'success': True, 'answer': reply})
