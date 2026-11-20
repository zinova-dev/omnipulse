import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

API_KEY = "omnipulse-secret-key-change-me"

@csrf_exempt
def receive_metrics(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    if request.headers.get("X-API-Key") != API_KEY:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "metrics",
        {
            "type": "metrics_message",
            "samples": [data],
        },
    )
    return JsonResponse({"status": "ok"})
