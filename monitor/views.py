import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import timedelta
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib.auth.models import User
from .models import MetricSnapshot

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

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

    MetricSnapshot.objects.create(
        server_name=data["server"],
        cpu=data["cpu"],
        memory=data["memory"],
    )

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "metrics",
        {
            "type": "metrics_message",
            "samples": [data],
        },
    )
    return JsonResponse({"status": "ok"})

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_history(request):
    server_name = request.GET.get("server")
    minutes = int(request.GET.get("minutes", 60))

    if not server_name:
        return Response({"error": "Server name is required"}, status=400)

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
    return Response({"data": data})

@api_view(["POST"])
@permission_classes([AllowAny])
def register_user(request):
    username = request.data.get("username")
    email = request.data.get("email")
    password = request.data.get("password")

    if not username or not password:
        return Response({"error": "Username e password são obrigatórios"}, status=400)
    
    if User.objects.filter(username=username).exists():
        return Response({"error": "Username já existe"}, status=400)

    try:
        User.objects.create_user(username=username, email=email, password=password)
        return Response({"status": "ok"})
    except Exception as e:
        return Response({"error": str(e)}, status=500)
    