from django.db import models

class MetricSnapshot(models.Model):
    server_name = models.CharField(max_length=100)
    cpu = models.FloatField()
    memory = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.server_name} - {self.timestamp}"
    