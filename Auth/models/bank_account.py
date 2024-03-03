from django.db import models


class UserBankDetail(models.Model):
    id = models.BigAutoField(primary_key=True)
    res_reference = models.CharField(max_length=255)
    user_name = models.CharField(max_length=255)
    user_email = models.CharField(max_length=255)
    account_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=255)
    bank_name = models.CharField(max_length=255)
    bank_code = models.CharField(max_length=255)
    account_status = models.CharField(max_length=255)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
