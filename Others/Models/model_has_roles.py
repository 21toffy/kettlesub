from django.db import models


class ModelHasRole(models.Model):
    role_id = models.BigIntegerField()
    model_type = models.CharField(max_length=255)
    model_id = models.BigIntegerField()
