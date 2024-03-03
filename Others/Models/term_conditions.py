from django.db import models


class TermCondition(models.Model):
    id = models.BigAutoField(primary_key=True)
    write_ups = models.TextField()
    admin = models.CharField(max_length=255)
    updated_by = models.CharField(max_length=255)
    created_at = models.DateTimeField(null=True, default=None)
    updated_at = models.DateTimeField(null=True, default=None)
