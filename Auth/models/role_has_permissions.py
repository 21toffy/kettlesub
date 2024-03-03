from django.db import models


class RoleHasPermissions(models.Model):
    permission_id = models.BigAutoField(primary_key=True)
    role_id = models.BigAutoField()
