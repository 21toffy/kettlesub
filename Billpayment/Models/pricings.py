from django.db import models

class Pricing(models.Model):
    id = models.BigAutoField(primary_key=True)
    product_id = models.CharField(max_length=11)
    provider = models.CharField(max_length=255)
    plan = models.CharField(max_length=255)
    price = models.CharField(max_length=255)
    validity = models.CharField(max_length=255)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
