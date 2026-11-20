import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import timedelta
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import MetricSnapshot

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

    # 1. Save to history
    MetricSnapshot.objects.create(
        server_name=data["server"],
        cpu=data["cpu"],
        memory=data["memory"],
    )

    # 2. Send in real-time via WebSocket
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "metrics",
        {
            "type": "metrics_message",
            "samples": [data],
        },
    )
    return JsonResponse({"status": "ok"})


@csrf_exempt
def get_history(request):
    server_name = request.GET.get("server")
    minutes = int(request.GET.get("minutes", 60))

    if not server_name:
        return JsonResponse({"error": "Server name is required"}, status=400)

    since = timezone.now() - timedelta(minutes=minutes)
    snapshots = MetricSnapshot.objects.filter(
        server_name=server_name, timestamp__gte=since
    ).order_by("timestamp")

    data = [
        {
            "server": s.server_name,
            "cpu": s.cpu,
            "memory": s.memory,
            "timestamp": s.timestamp.timestamp(),
        }
        for s in snapshots
    ]
    return JsonResponse({"data": data})
