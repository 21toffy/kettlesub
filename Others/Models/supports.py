from django.db import models


class Support(models.Model):
    id = models.BigAutoField(primary_key=True)
    page_type = models.CharField(max_length=255)
    page_name = models.CharField(max_length=255)
    page_link = models.CharField(max_length=255)
    page_icon = models.TextField()
    created_at = models.DateTimeField(null=True, default=None)
    updated_at = models.DateTimeField(null=True, default=None)
