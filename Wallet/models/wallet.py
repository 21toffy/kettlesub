from django.core.validators import MinValueValidator
from Common.models import BaseModel
from django.db import models


class WalletModel(BaseModel):
    WALLET_TYPE = [
        ("MAIN", "MAIN"),
        ("BONUS", "BONUS"),
    ]
    user = models.ForeignKey(
        "Auth.User", on_delete=models.CASCADE, related_name="user_wallet"
    )
    balance = models.DecimalField(max_digits=20, decimal_places=2, default=0.0, validators=[MinValueValidator(0.0)])
    currency = models.CharField(max_length=255)
    wallet_type = models.CharField(choices=WALLET_TYPE, max_length=255)

    class Meta:
        db_table = "wallets"
        managed = True
        verbose_name = "Wallet"
        verbose_name_plural = "Wallets"


