from django.db import models


class LocalGovernment(models.Model):
    id = models.IntegerField(primary_key=True)
    state_id = models.IntegerField()
    lga_name = models.CharField(max_length=255)
