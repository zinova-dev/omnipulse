import json
import random
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import timedelta
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from .models import MetricSnapshot, EmailVerification

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

    if not username or not password or not email:
        return Response({"error": "Username, email and password are required"}, status=400)
    
    if User.objects.filter(username=username).exists():
        return Response({"error": "Username already exists"}, status=400)

    if User.objects.filter(email=email).exists():
        return Response({"error": "Email already registered"}, status=400)

    try:
        user = User.objects.create_user(username=username, email=email, password=password, is_active=False)
        
        code = str(random.randint(100000, 999999))
        EmailVerification.objects.create(user=user, code=code)
        
        send_mail(
            "OmniPulse - Account Verification",
            f"Your verification code is: {code}",
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        
        return Response({"status": "ok", "message": "Account created. Please check your email."})
    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(["POST"])
@permission_classes([AllowAny])
def verify_email(request):
    username = request.data.get("username")
    code = request.data.get("code")

    if not username or not code:
        return Response({"error": "Username and code are required"}, status=400)

    try:
        user = User.objects.get(username=username)
        verification = EmailVerification.objects.get(user=user)

        if verification.code == code:
            user.is_active = True
            user.save()
            verification.delete()
            return Response({"status": "ok", "message": "Email verified successfully."})
        else:
            return Response({"error": "Invalid verification code."}, status=400)
    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=404)
    except EmailVerification.DoesNotExist:
        return Response({"error": "No verification code found for this user."}, status=404)
    