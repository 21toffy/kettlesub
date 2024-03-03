from django.db import models


class PaymentGateway(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    secret_key = models.CharField(max_length=255)
    public_key = models.CharField(max_length=255)
    callback_url = models.CharField(max_length=255)
    webhook_url = models.CharField(max_length=255)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
