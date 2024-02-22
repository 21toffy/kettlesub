from Common.models import BaseModel
from django.db import models
from Auth.models.user import User


class UserBankAccount(BaseModel):
    user = models.OneToOneField(
        User, related_name="USER_bank", on_delete=models.CASCADE
    )
    bank_name = models.CharField(max_length=200)
    bank_code = models.CharField(max_length=10, blank=True)
    account_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=10)

    class Meta:
        verbose_name_plural = "Banks Accounts"
        db_table = "bank_accounts"

    def __str__(self) -> str:
        return f"{self.account_name} - {self.account_number}"