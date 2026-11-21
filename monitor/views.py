
import json
import logging
import os
import random
import urllib.error
import urllib.request

from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import MetricSnapshot, EmailVerification

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response


logger = logging.getLogger(__name__)

API_KEY = "omnipulse-secret-key-change-me"


def send_verification_email(email, code):
    """
    Envia o código de verificação através da API HTTPS da Brevo.
    """

    api_key = os.environ.get("BREVO_API_KEY")
    sender_email = settings.DEFAULT_FROM_EMAIL

    if not api_key:
        raise RuntimeError("BREVO_API_KEY não está configurada.")

    if not sender_email:
        raise RuntimeError("DEFAULT_FROM_EMAIL não está configurado.")

    payload = {
        "sender": {
            "name": "OmniPulse",
            "email": sender_email,
        },
        "to": [
            {
                "email": email,
            }
        ],
        "subject": "OmniPulse - Account Verification",
        "textContent": (
            f"Welcome to OmniPulse!\n\n"
            f"Your email verification code is: {code}\n\n"
            f"Enter this code in OmniPulse to activate your account."
        ),
    }

    request = urllib.request.Request(
        url="https://api.brevo.com/v3/smtp/email",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "accept": "application/json",
            "api-key": api_key,
            "content-type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            if response.status not in (200, 201, 202):
                raise RuntimeError(
                    f"Brevo respondeu com HTTP {response.status}."
                )

            return json.loads(response.read().decode("utf-8"))

    except urllib.error.HTTPError as error:
        response_body = error.read().decode("utf-8", errors="replace")
        logger.error(
            "Brevo API HTTP error %s: %s",
            error.code,
            response_body,
        )
        raise RuntimeError(
            f"Brevo recusou o envio do email (HTTP {error.code})."
        ) from error

    except urllib.error.URLError as error:
        logger.error("Erro de ligação à Brevo: %s", error.reason)
        raise RuntimeError(
            "Não foi possível estabelecer ligação à API da Brevo."
        ) from error


@csrf_exempt
def receive_metrics(request):
    if request.method != "POST":
        return JsonResponse(
            {"error": "Method not allowed"},
            status=405,
        )

    if request.headers.get("X-API-Key") != API_KEY:
        return JsonResponse(
            {"error": "Unauthorized"},
            status=401,
        )

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {"error": "Invalid JSON"},
            status=400,
        )

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
        return Response(
            {"error": "Server name is required"},
            status=400,
        )

    since = timezone.now() - timedelta(minutes=minutes)

    snapshots = MetricSnapshot.objects.filter(
        server_name=server_name,
        timestamp__gte=since,
    ).order_by("timestamp")

    data = [
        {
            "server": snapshot.server_name,
            "cpu": snapshot.cpu,
            "memory": snapshot.memory,
            "timestamp": snapshot.timestamp.timestamp(),
        }
        for snapshot in snapshots
    ]

    return Response({"data": data})


@api_view(["POST"])
@permission_classes([AllowAny])
def register_user(request):
    username = request.data.get("username")
    email = request.data.get("email")
    password = request.data.get("password")

    if not username or not password or not email:
        return Response(
            {
                "error": "Username, email and password are required"
            },
            status=400,
        )

    if User.objects.filter(username=username).exists():
        return Response(
            {"error": "Username already exists"},
            status=400,
        )

    if User.objects.filter(email=email).exists():
        return Response(
            {"error": "Email already registered"},
            status=400,
        )

    try:
        with transaction.atomic():
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_active=False,
            )

            code = str(random.randint(100000, 999999))

            EmailVerification.objects.create(
                user=user,
                code=code,
            )

            send_verification_email(email, code)

        return Response(
            {
                "status": "ok",
                "message": (
                    "Account created. Please check your email."
                ),
            }
        )

    except Exception:
        logger.exception(
            "Falha ao registar utilizador ou enviar email de verificação."
        )

        return Response(
            {
                "error": (
                    "Não foi possível concluir o registo ou enviar "
                    "o email de verificação. Tenta novamente."
                )
            },
            status=502,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def verify_email(request):
    username = request.data.get("username")
    code = request.data.get("code")

    if not username or not code:
        return Response(
            {"error": "Username and code are required"},
            status=400,
        )

    try:
        user = User.objects.get(username=username)

        verification = EmailVerification.objects.get(user=user)

        if verification.code == code:
            user.is_active = True
            user.save()

            verification.delete()

            return Response(
                {
                    "status": "ok",
                    "message": "Email verified successfully.",
                }
            )

        return Response(
            {"error": "Invalid verification code."},
            status=400,
        )

    except User.DoesNotExist:
        return Response(
            {"error": "User not found."},
            status=404,
        )

    except EmailVerification.DoesNotExist:
        return Response(
            {
                "error": (
                    "No verification code found for this user."
                )
            },
            status=404,
        )

