from Auth.models import User
from django.db import models
from Wallet.models import WalletModel
from Common.models import BaseModel


class TransactionModel(BaseModel):
    """
    Model structure for a transaction record
    """

    TRANSACTION_TYPE = (
        ("Credit", "Credit"),
        ("Debit", "Debit"),
    )
    TRANSACTION_CURRENCY = (
        ("NGN", "NGN"),
    )

    CHANNEL = (
        ("WEB", "WEB"),
        ("APP", "APP"),
    )

    TRANSACTION_STATUS = (
        ("1", "Processing"),
        ("2", "Success"),
        ("3", "Failed"),
        ("4", "Declined"),
        ("4", "Refunded"),
    )

    CATEGORY = (
        ("BILLS", "BILLS"),
        ("CARD", "CARD"),
        ("REFERRARL", "REFERRARL"),
        ("AIRTIME_PAYMENT", "Airtime"),
        ("DATA_PAYMENT", "Data"),
        ("ELECTRICITY_BILL", "Electricity"),
        ("WALLET_TRANSFER", "Wallet Transfer"),
        ("BANK_TRANSFER", "Bank Tran Transfer"),
        ("CARD_MAINTANANCE", "Card maintenance"),
        ("CARD_DEBIT", "Card Debit"),
        ("CARD_CREDIT", "Card Credit"),
        ("WALLET_CREDIT", "Wallet Credit"),
        ("WALLET_DEBIT", "Wallet Debit"),
        ("CABLE", "CABLE"),
        ("CARD_FUNDING", "Card Funding"),
        ("CARD_FUNDING_FEE", "CARD_FUNDING_FEE")
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    wallet = models.ForeignKey(
        WalletModel, on_delete=models.SET_NULL, null=True)
    transaction_type = models.CharField(choices=TRANSACTION_TYPE, max_length=10)
    reference = models.CharField(max_length=100)
    ext_reference = models.CharField(max_length=100, null=True)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(
        choices=TRANSACTION_STATUS, null=True, max_length=255)
    channel = models.CharField(
        choices=CHANNEL, default='APP', null=True, max_length=255)
    category = models.CharField(choices=CATEGORY, null=True, max_length=50)
    transaction_context = models.JSONField(default=dict, null=True, blank=True)
    failed_transaction_context = models.JSONField(
        default=dict, null=True, blank=True)
    balance_before = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True, default=0.00
    )
    balance_after = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True, default=0.00
    )
    currency = models.CharField(choices=TRANSACTION_CURRENCY, default='NGN', null=True, max_length=255)


    def __str__(self):
        return self.reference + " " + str(self.created_at)


    @classmethod
    def retrieve(cls, **query):
        return cls.objects.filter(**query)


    class Meta:
        db_table = "transactions"
        managed = True
        verbose_name = "Transactions"
        verbose_name_plural = "Transactions"
