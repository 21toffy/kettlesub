from django.db import models


class KYC(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_id = models.BigAutoField()
    countryC_code = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    middle_name = models.CharField(max_length=255, null=True, blank=True)
    transaction_ref = models.CharField(max_length=255)
    bvn_number = models.CharField(max_length=255)
    id_card = models.CharField(max_length=255)
    date_of_birth = models.CharField(max_length=255)
    photo = models.CharField(max_length=255, null=True, blank=True)
    gender = models.CharField(max_length=6, null=True, blank=True)
    state_of_origin = models.CharField(max_length=255, null=True, blank=True)
    lga_of_origin = models.CharField(max_length=255, null=True, blank=True)
    email = models.CharField(max_length=255, null=True, blank=True)
    phoneNumber = models.BigIntegerField(null=True, blank=True)
    verify_status = models.CharField(max_length=255)
    verificationStatus = models.BooleanField(default=False)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
