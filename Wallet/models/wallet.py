from django.db import models


class Wallet(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_id = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    balance = models.CharField(max_length=255)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
