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


class User(BaseModel, AbstractBaseUser):
    email = models.EmailField(
        verbose_name="email address",
        max_length=255,
        unique=True,
    )
    phone = models.CharField(
        unique=True, help_text="Phone number", max_length=25, null=True
    )
    password = models.CharField(max_length=255, null=True)
    first_name = models.CharField(max_length=255, null=True)
    middle_name = models.CharField(max_length=255, null=True)
    last_name = models.CharField(max_length=255, null=True)
    username = models.CharField(max_length=255, null=True)
    referal_code = models.CharField(max_length=255, null=True)
    username = models.CharField(max_length=255, null=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    ussd_pin = models.CharField(
        max_length=50, null=True, blank=True)
    is_flagged = models.BooleanField(default=False)
    is_frozen = models.BooleanField(default=False)
    objects = MyUserManager()

    USERNAME_FIELD = "email"

    class Meta:
        db_table = "users"
        managed = True
        verbose_name = "User"
        verbose_name_plural = "User"

    def get_name(self):
        full_name = " ".join(
            filter(None, [self.first_name, self.middle_name, self.last_name]))
        return full_name
