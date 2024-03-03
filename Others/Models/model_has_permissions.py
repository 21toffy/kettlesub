from django.db import models


class ModelHasPermission(models.Model):
    permission_id = models.BigIntegerField()
    model_type = models.CharField(max_length=255)
    model_id = models.BigIntegerField()
