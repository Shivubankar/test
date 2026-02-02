from pathlib import Path
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods
from .models import AIConversation, AIMessage, AIDocument
from audit.ollama_service import generate_ai_response


MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.txt', '.xls', '.xlsx'}


def _extract_text(file_obj, filename):
    ext = Path(filename).suffix.lower()
    if ext == '.pdf':
        try:
            import pdfplumber
        except ImportError as exc:
            raise RuntimeError('pdfplumber is required for PDF extraction') from exc
        file_obj.seek(0)
        with pdfplumber.open(file_obj) as pdf:
            pages = [page.extract_text() or '' for page in pdf.pages]
        return '\n'.join(pages).strip()

    if ext == '.docx':
        try:
            from docx import Document
        except ImportError as exc:
            raise RuntimeError('python-docx is required for DOCX extraction') from exc
        file_obj.seek(0)
        doc = Document(file_obj)
        return '\n'.join(p.text for p in doc.paragraphs).strip()

    if ext in {'.xls', '.xlsx'}:
        try:
            import pandas as pd
        except ImportError as exc:
            raise RuntimeError('pandas is required for Excel extraction') from exc
        file_obj.seek(0)
        df = pd.read_excel(file_obj)
        return df.to_string(index=False).strip()

    if ext == '.txt':
        file_obj.seek(0)
        raw = file_obj.read()
        if isinstance(raw, bytes):
            return raw.decode('utf-8', errors='ignore').strip()
        return str(raw).strip()

    raise RuntimeError('Unsupported file type')


@login_required
@require_http_methods(["GET"])
def ai_assistant_home(request):
    conversations = AIConversation.objects.filter(user=request.user).order_by('-created_at')
    conversation_id = request.GET.get('conversation')
    active_conversation = None
    messages = []

    if conversation_id:
        active_conversation = get_object_or_404(
            AIConversation, id=conversation_id, user=request.user
        )
    elif conversations.exists():
        active_conversation = conversations.first()

    if active_conversation:
        messages = active_conversation.messages.order_by('created_at')

    documents = AIDocument.objects.filter(user=request.user).order_by('-created_at')
    context = {
        'conversations': conversations,
        'active_conversation': active_conversation,
        'messages': messages,
        'documents': documents,
    }
    return render(request, 'ai_assistant/chat.html', context)


@login_required
@require_http_methods(["POST"])
def upload_document(request):
    file_obj = request.FILES.get('document')
    if not file_obj:
        return JsonResponse({'success': False, 'error': 'No file provided.'}, status=400)

    ext = Path(file_obj.name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return JsonResponse({'success': False, 'error': 'Unsupported file type.'}, status=400)

    if file_obj.size > MAX_UPLOAD_SIZE:
        return JsonResponse({'success': False, 'error': 'File exceeds 10MB limit.'}, status=400)

    try:
        extracted_text = _extract_text(file_obj, file_obj.name)
        file_obj.seek(0)
    except Exception as exc:
        return JsonResponse({'success': False, 'error': str(exc)}, status=400)

    doc = AIDocument.objects.create(
        user=request.user,
        file=file_obj,
        extracted_text=extracted_text
    )

    return JsonResponse({
        'success': True,
        'document': {
            'id': doc.id,
            'name': os.path.basename(doc.file.name),
        }
    })


@login_required
@require_http_methods(["POST"])
def send_message(request):
    content = request.POST.get('message', '').strip()
    conversation_id = request.POST.get('conversation_id')
    if not content:
        return JsonResponse({'success': False, 'error': 'Message is empty.'}, status=400)

    if conversation_id:
        conversation = get_object_or_404(
            AIConversation, id=conversation_id, user=request.user
        )
    else:
        title = content[:50] if len(content) > 50 else content
        conversation = AIConversation.objects.create(user=request.user, title=title or 'New Conversation')

    AIMessage.objects.create(conversation=conversation, role=AIMessage.ROLE_USER, content=content)

    documents = AIDocument.objects.filter(user=request.user).order_by('-created_at')
    context_text = ''
    if documents.exists():
        combined = '\n\n'.join(doc.extracted_text for doc in documents if doc.extracted_text)
        context_text = combined[:20000]

    prompt = content
    if context_text:
        prompt = f"Document context:\n{context_text}\n\nUser question:\n{content}"

    try:
        assistant_reply = generate_ai_response(prompt)
    except Exception as exc:
        return JsonResponse({'success': False, 'error': str(exc)}, status=503)

    AIMessage.objects.create(
        conversation=conversation,
        role=AIMessage.ROLE_ASSISTANT,
        content=assistant_reply
    )

    return JsonResponse({
        'success': True,
        'conversation_id': conversation.id,
        'answer': assistant_reply
    })
