from django.db import models
from django.contrib.auth.models import User

class MetricSnapshot(models.Model):
    server_name = models.CharField(max_length=100)
    cpu = models.FloatField()
    memory = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.server_name} - {self.timestamp}"

class EmailVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.code}"
    