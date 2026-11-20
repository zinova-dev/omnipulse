from django.contrib import admin
from django.urls import path
from monitor.views import receive_metrics, get_history, register_user, verify_email
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/metrics/", receive_metrics, name="receive_metrics"),
    path("api/history/", get_history, name="get_history"),
    path("api/register/", register_user, name="register_user"),
    path("api/verify-email/", verify_email, name="verify_email"),
]
