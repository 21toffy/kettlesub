from django.db import models



class ReferralBonus(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_id = models.IntegerField()
    amount = models.BigIntegerField()
    balance_before = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
