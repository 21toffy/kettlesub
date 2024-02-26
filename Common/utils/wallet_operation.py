import uuid
from decimal import Decimal
from datetime import datetime
from Wallet.models.wallet import WalletModel
from Transactions.models import TransactionModel
from celery.loaders import app
from django.db import transaction
from django.db.models import F


def debit_credit_user_wallet(
    user,
    wallet_type,
    amount,
    ref,
    wallet_id,
    action="debit",
    description=None,
    transaction_context=None,
):
    category_type = (
        "AIRTIME_PAYMENT" if app == "Airtime"
        else "DATA_PAYMENT" if app == "Data"
        else "ELECTRICITY_BILL" if app == "Electricity"
        else "CABLE" if app == "DSTV"
        else "EXTERNAL_CREDIT" if app == "VFD" and action == "credit"
        else "EXTERNAL_DEBIT" if app == "settlement" and action == "debit"
        else "EXTERNAL_DEBIT" if app == "settlement" and action == "debit"
        else "FEE" if app == "TRANSFER_FEE"
        else "PAYMENT"
    )

    try:
        with transaction.atomic() as initial_save_point:
            start_time = datetime.now()
            print(f"***************Start Time***************: {start_time} for {ref}")
            txRefDebit = "{}".format(uuid.uuid4().int)
            if description is None:
                description = "Wallet " + action

            wallet_object = WalletModel.objects.filter(id=wallet_id).select_for_update().first()

            amount_before = WalletModel.objects.filter(id=wallet_id).values('balance').first()['balance']
            if action == "debit":
                WalletModel.objects.filter(id=wallet_object.id).update(balance=F("balance") - amount)
                txRefDebit = "Dr" + txRefDebit[-8:]
                amount_after = WalletModel.objects.get(id=wallet_object.id).balance
            else:
                WalletModel.objects.filter(id=wallet_object.id).update(balance=F("balance") + amount)
                txRefDebit = "Cr" + txRefDebit[-8:]
                amount_after = WalletModel.objects.get(user_id=user.id, id=wallet_object.id).balance

            data = {
                "reference": txRefDebit,
                "user": user,
                "ext_reference": ref,
                "amount": amount,
                "status": "1",
                "wallet": wallet_object,
                "type": str(action).title(),
                "description": description,
                "category": category_type,
                "transaction_context": transaction_context,
            }

            try:
                txn = TransactionModel.objects.create(
                    reference=txRefDebit,
                    user=user,
                    ext_reference=ref,
                    amount=amount,
                    status="1",
                    wallet=wallet_object,
                    type=str(action).title(),
                    description=description,
                    category=category_type,
                    transaction_context=transaction_context,
                    balance_before=Decimal(amount_before),
                    balance_after=Decimal(amount_after),
                )
                return True, initial_save_point, txn.id

            except Exception as e:
                print("+++++++++++++++++++++++++++++++++++++++++++++=")
                print(data, "THIS DATA")
                print(str(e))
                return False, str(e), ""

    except Exception as error:
        print(error, 111111111111)
        transaction.savepoint_rollback(initial_save_point)
        return False, "", ""
