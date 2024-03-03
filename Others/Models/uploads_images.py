from django.db import models


class UploadImage(models.Model):
    id = models.BigAutoField(primary_key=True)
    subject = models.CharField(max_length=255)
    message = models.CharField(max_length=255)
    image = models.CharField(max_length=255, default=None)
    created_at = models.DateTimeField(null=True, default=None)
    updated_at = models.DateTimeField(null=True, default=None)
