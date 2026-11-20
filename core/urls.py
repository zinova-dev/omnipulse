from django.contrib import admin
from django.urls import path
from monitor.views import receive_metrics, get_history

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/metrics/", receive_metrics),
    path("api/history/", get_history),
]
