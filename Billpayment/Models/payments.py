from django.db import models


class Payment(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_id = models.CharField(max_length=255)
    currency = models.CharField(max_length=255)
    reference = models.CharField(max_length=255)
    amount = models.CharField(max_length=255)
    payment_id = models.CharField(max_length=255)
    message = models.CharField(max_length=255)
    payment_mode = models.CharField(max_length=255)
    status = models.CharField(max_length=255)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
