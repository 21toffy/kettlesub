from django.db import models


class Migration(models.Model):
    id = models.PositiveIntegerField(primary_key=True)
    migration = models.CharField(max_length=255)
    batch = models.IntegerField()
