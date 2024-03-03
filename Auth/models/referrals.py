from django.db import models

class Referral(models.Model):
    id = models.BigAutoField(primary_key=True)
    referral = models.CharField(max_length=255)
    referree_id = models.CharField(max_length=255)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
