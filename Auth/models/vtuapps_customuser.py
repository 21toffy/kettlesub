from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

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

        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    id = models.BigAutoField(primary_key=True)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    FullName = models.CharField(max_length=200, null=True, blank=True)
    Address = models.CharField(max_length=500, null=True, blank=True)
    BankName = models.CharField(max_length=100)
    AccountNumber = models.CharField(max_length=40)
    Phone = models.CharField(max_length=30)
    AccountName = models.CharField(max_length=200)
    Account_Balance = models.FloatField(null=True, blank=True)
    pin = models.CharField(max_length=5, null=True, blank=True)
    referer_username = models.CharField(max_length=50, null=True, blank=True)
    first_payment = models.BooleanField(default=False)
    Referer_Bonus = models.FloatField(null=True, blank=True)
    user_type = models.CharField(max_length=30, null=True, blank=True)
    reservedaccountNumber = models.CharField(max_length=100, null=True, blank=True)
    reservedbankName = models.CharField(max_length=100, null=True, blank=True)
    reservedaccountReference = models.CharField(max_length=100, null=True, blank=True)
    Bonus = models.FloatField(null=True, blank=True)
    verify = models.BooleanField(default=False)
    DOB = models.DateField(null=True, blank=True)
    Gender = models.CharField(max_length=6, null=True, blank=True)
    State_of_origin = models.CharField(max_length=100, null=True, blank=True)
    Local_gov_of_origin = models.CharField(max_length=100, null=True, blank=True)
    BVN = models.CharField(max_length=50, null=True, blank=True)
    passport_photogragh = models.CharField(max_length=100, null=True, blank=True)
    accounts = models.TextField(null=True, blank=True)
    traffic_source = models.CharField(max_length=30, null=True, blank=True)
    email_verify = models.BooleanField(default=False)
    webhook = models.CharField(max_length=200, null=True, blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

