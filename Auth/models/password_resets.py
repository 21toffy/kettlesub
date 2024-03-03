from django.db import models


class PasswordReset(models.Model):
    email = models.CharField(max_length=255, primary_key=True)
    token = models.CharField(max_length=255)
    created_at = models.DateTimeField(null=True, blank=True)
