from django.db import models


class Product(models.Model):
    id = models.BigAutoField(primary_key=True)
    category_code = models.CharField(max_length=255, default=None)
    operator_code = models.CharField(max_length=255, default=None)
    product_code = models.CharField(max_length=255, default=None)
    product_name = models.TextField(default=None)
    plan_value = models.CharField(max_length=255, default=None)
    product_price = models.BigIntegerField(default=None)
    topUser_price = models.BigIntegerField(default=None)
    affiliates_price = models.BigIntegerField(default=None)
    gold_price = models.BigIntegerField(default=None)
    platinum_price = models.BigIntegerField(default=None)
    validity = models.CharField(max_length=255, default=None)
    status = models.BooleanField(default=False)
    created_at = models.DateTimeField(null=True, default=None)
    updated_at = models.DateTimeField(null=True, default=None)
