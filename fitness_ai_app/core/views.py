import json
import os

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from openai import OpenAI


def splash(request):
    return render(request, 'core/splash.html')


def chat_page(request):
    return render(request, 'core/chat.html')


@csrf_exempt
@require_http_methods(["POST"])
def api_chat(request):
    try:
        body = json.loads(request.body)
        messages = body.get("messages", [])
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    if not messages:
        return JsonResponse({"error": "messages list is required."}, status=400)

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return JsonResponse({"error": "OPENAI_API_KEY not configured."}, status=500)

    client = OpenAI(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=messages,
        )
        reply = response.choices[0].message.content
        return JsonResponse({"reply": reply})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=502)
