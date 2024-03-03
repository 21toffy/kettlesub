from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from Common.models import BaseModel
from django.db import models


class MyUserManager(BaseUserManager):
    def create_user(self, email, password=None):
        """
        Creates and saves a User
        """
        if not email:
            raise ValueError("Users must have an email address")
        user = self.model(
            email=self.normalize_email(email),
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        """
        Creates and saves a user
        """
        user = self.create_user(
            email,
            password,
        )
        user.is_admin = True
        user.save(using=self._db)
        return user




class User(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    username = models.CharField(max_length=255)
    last_login = models.DateTimeField(null=True, blank=True)
    mobile = models.CharField(max_length=255)
    create_pin = models.CharField(max_length=255)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    password = models.CharField(max_length=255)
    package = models.CharField(max_length=255)
    refered_by = models.CharField(max_length=255, null=True, blank=True)
    remember_token = models.CharField(max_length=100, null=True, blank=True)
    hearFrom = models.CharField(max_length=255, null=True, blank=True)
    role = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
