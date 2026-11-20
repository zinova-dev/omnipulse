from django.contrib import admin
from django.urls import path
from monitor.views import receive_metrics

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/metrics/", receive_metrics),
]
