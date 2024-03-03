from django.db import models


class Job(models.Model):
    id = models.BigAutoField(primary_key=True)
    queue = models.CharField(max_length=255)
    payload = models.TextField()
    attempts = models.SmallIntegerField()
    reserved_at = models.IntegerField(null=True, blank=True)
    available_at = models.IntegerField()
    created_at = models.IntegerField()
