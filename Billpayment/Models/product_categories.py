from django.db import models


class ProductCategory(models.Model):
    id = models.BigAutoField(primary_key=True)
    operator_code = models.CharField(max_length=255)
    category_code = models.CharField(max_length=255)
    category_name = models.TextField()
    status = models.BooleanField(default=False)
    created_at = models.DateTimeField(null=True, default=None)
    updated_at = models.DateTimeField(null=True, default=None)
