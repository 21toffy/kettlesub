
from django.urls import path
from Wallet.views.wallet import *

urlpatterns = [
    path('set-pin/', SetPin.as_view(), name='set-pin'),
    path('get-wallet-balance/', GetWalletBalanceView.as_view(), name='get-wallet-balance'),
    path('wallet-transfer/', WalletTransferView.as_view(), name='wallet-transfer'),
]
