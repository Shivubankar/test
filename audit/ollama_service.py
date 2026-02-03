import json
import urllib.request
import urllib.error


def generate_ai_response(prompt):
    if not prompt or not str(prompt).strip():
        return ''

    payload = {
        'model': 'llama3',
        'prompt': str(prompt),
        'stream': False,
    }

    data = json.dumps(payload).encode('utf-8')
    request = urllib.request.Request(
        'http://localhost:11434/api/generate',
        data=data,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode('utf-8')
            parsed = json.loads(body)
            return str(parsed.get('response', '')).strip()
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise RuntimeError('AI Assistant is offline. Please start Ollama.') from exc
    except Exception as exc:
        raise RuntimeError('Unable to generate AI response.') from exc
