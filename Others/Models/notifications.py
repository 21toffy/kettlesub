from django.db import models


class Notification(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_id = models.CharField(max_length=255)
    message = models.TextField()
    status = models.BooleanField(default=False)
    created_at = models.DateTimeField(null=True, default=None)
    updated_at = models.DateTimeField(null=True, default=None)
