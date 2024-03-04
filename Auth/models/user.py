from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.BigAutoField(primary_key=True)
    password = models.CharField(max_length=255, default='123456789')
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255, blank=True)
    username = models.CharField(max_length=255, unique=True, null=True)
    last_login = models.DateTimeField(null=True, blank=True)
    mobile = models.CharField(max_length=255, blank=True, null=True)
    create_pin = models.CharField(max_length=255, default='0000')
    email_verified_at = models.DateTimeField(null=True, blank=True)
    package = models.CharField(max_length=255, blank=True)
    refered_by = models.CharField(max_length=255, null=True, blank=True)
    remember_token = models.CharField(max_length=100, null=True, blank=True)
    hearFrom = models.CharField(max_length=255, null=True, blank=True)
    role = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email
