from django.db import models

class Fund(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_id = models.IntegerField(default=0)
    amount = models.CharField(max_length=255, default='0')
    fund_by = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
