from django.db import models


class History(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_id = models.CharField(max_length=255)
    network = models.CharField(max_length=255, null=True, blank=True)
    api_mode = models.CharField(max_length=255)
    purchase = models.CharField(max_length=255)
    plan = models.CharField(max_length=255)
    product_code = models.CharField(max_length=255)
    transfer_ref = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=255)
    distribe_ref = models.CharField(max_length=255)
    selling_price = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    send_value = models.IntegerField()
    deviceNo = models.TextField()
    commission_applied = models.CharField(max_length=255)
    processing_state = models.CharField(max_length=255)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
