from rest_framework.views import APIView
from Merchant.serializers import *
from django.conf import settings
from Ups.util.remote import makeRemoteCall
from rest_framework.response import Response
import requests
import json
import uuid
from rest_framework import status, permissions
from Billpayment.serializers import BillPaymentSerializer
from django.db import transaction
from Wallet.utils.wallet import WalletUtilities

from Billpayment.utils import airtime_provider_image
from Notification.tasks import (
    track_user_activity,
    send_email_notification_async,
)
from Notification.utils.notification_utils import NotificationManager

from Billpayment.views.id_verification import verify_id
from Transactions.tasks import (
    update_transaction_status,
    create_profit_transaction,
    refund_user_wallet,
)
from Wallet.models import WalletModel
import idpaybackendengine.error_code as error_code
from django.conf import settings
from helpers.money import format_currency
from helpers.error_webhooks import TeamsErrorManager, GatewayException
from common.mixins.service_providers import GovaMixin, BaxiMixin

# error_code.TIER_2_AIRTIME_DAILY_LIMIT

from helpers.baxi_helpers import mocked_transactions, extract_data_from_baxi


class ListAirtimeProviders(BaxiMixin, APIView):
    def get(self, request):
        try:
            url = f"{settings.BAXI_BASE_URL}services/airtime/providers"
            post_data = {}
            params = {}
            header = {
                "Authorization": "Api-key " + settings.BAXI_BAP_ACCESS_KEY,
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
            method = requests.get

            airtime_providers = makeRemoteCall(
                url, post_data, params, header, method
            )
            to_json = airtime_providers.json()
            if to_json["status"] == "success" and to_json["code"] == 200:
                response_data = to_json["data"]
                # print(response_data)

                # update data with provider images
                for element in response_data["providers"]:
                    # element["image"] = airtime_provider_image[
                    #     element["service_type"]
                    # ]
                    element["image"] = airtime_provider_image.get(element["service_type"], "")

                # print(response_data, 111)
                response_data = {
                    "status": True,
                    "data": response_data,
                    "code": "SUCCESS",
                }
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                response_data = {
                    "status": False,
                    "data": to_json["message"],
                    "code": "PROCESS_FAILED",
                }
                return Response(
                    response_data, status=status.HTTP_417_EXPECTATION_FAILED
                )
        except Exception as error:
            # print("heeeeeeeeere")

            response_data = {
                "status": False,
                "data": "{}".format(error),
                "code": "UNKNOWN_ERROR",
            }
            return Response(
                response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MakeAirtimeBillPayment(GovaMixin, BaxiMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        payment_serializer = BillPaymentSerializer(data=request.data)
        currency = "NGN"
        save_point_rollback = ""
        transfer_type = "BILL_PAYMENT"
        try:
            plan = "prepaid"
            response_data = {}
            agent_id = settings.BAXI_AGENT_ID
            user = request.user
            if payment_serializer.is_valid():
                # generate AgentRef and AgentId
                agent_ref = "AT" + "{}".format(uuid.uuid4().int)
                service_type = payment_serializer.data.get("service_type")
                amount = payment_serializer.data.get("amount")
                phone = payment_serializer.data.get("phone")
                device_id = payment_serializer.data["device_id"]

                verification_type = payment_serializer.data.get(
                    "verification_type"
                )
                # check wallet address balance
                with transaction.atomic():
                    WalletModel.objects.filter(user=request.user, currency="NGN").select_for_update().first()
                    wallet_balance = WalletUtilities.get_single_balance(
                        self, user, 1
                    )

                    (
                        tier_status,
                        tier_response,
                    ) = WalletUtilities.tier_transaction_check(
                        request.user, wallet_balance, amount, transfer_type
                    )
                    if not tier_status:
                        return tier_response

                    mock = False
                    if not mock:
                        flag, flag_message = self.compareBalanceWithServiceAmount(
                            float(wallet_balance.balance), float(amount)
                        )
                    else:
                        import random

                        result = [
                            [True, "success"],
                            [False, "Your wallet balance is low"],
                        ]
                        selected_item = random.choice(result)

                        # flag, flag_message  = selected_item[0], selected_item[1]
                        flag, flag_message = True, "success"

                    if not flag:
                        response_data = {
                            "status": False,
                            "data": flag_message,
                            "code": "INSUFFICIENT_BALANCE",
                            "message": "You have a low wallet balance",
                        }
                        track_user_activity.delay(
                            action="airtime purchase failed",
                            actor_email=request.user.email,
                        )
                        # NotificationManager.fcm_notification_task(
                        #     title="Airtime Purchase",
                        #     body="You have a low wallet balance",
                        #     reciever_email=user.email,
                        # )
                        return Response(
                            response_data,
                            status=status.HTTP_417_EXPECTATION_FAILED,
                        )

                    else:
                        # process to make service and debit user wallet
                        # compare face sent
                        if not mock:
                            verify_flag, verify_message = verify_id(
                                verification_type=verification_type,
                                verification_value=payment_serializer.data.get(
                                    "verification_value"
                                ),
                                user=request.user,
                                device_id=device_id,
                            )
                        else:
                            verify_flag, verify_message = True, ""

                        if not verify_flag:
                            return Response(
                                error_code.UNABLE_TO_VERIFY_USER,
                                status=status.HTTP_417_EXPECTATION_FAILED,
                            )

                        # start bill transaction
                        data = json.dumps(
                            {
                                "agentReference": agent_ref,
                                "agentId": agent_id,
                                "plan": plan,
                                "service_type": service_type,
                                "amount": amount,
                                "phone": phone,
                            }
                        )
                        dict_data = {
                            "agentReference": agent_ref,
                            "agentId": agent_id,
                            "plan": plan,
                            "service_type": service_type,
                            "amount": amount,
                            "phone": phone,
                        }

                        from Wallet.utils.spending_limit import rate_limiting

                        stats, mess = rate_limiting(
                            request.user, "Airtime", amount, phone
                        )
                        if not stats:
                            return Response(
                                error_code.POSSIBLE_DUPLICATE_TRANSACTION,
                                status=status.HTTP_417_EXPECTATION_FAILED,
                            )

                        # debit wallet
                        (
                            debit_wallet,
                            save_point_rollback,
                            transaction_id,
                        ) = WalletUtilities.debit_credit_user_wallet(
                            self,
                            user,
                            1,
                            amount,
                            agent_ref,
                            wallet_balance,
                            app="Airtime",
                            # phone = phone,
                        )

                    url = f"{settings.BAXI_BASE_URL}services/airtime/request"

                    if debit_wallet:
                        if not mock:
                            res = self.loadAirtime(data, url)
                        else:
                            import random

                            random_transaction = random.choice(
                                mocked_transactions
                            )
                            res = extract_data_from_baxi(random_transaction)

                        # print("YYYYYYYYYYYYYYYYY")
                        # print(res)
                        # print(res["status"], res["requery"])
                        # print("MMMMMMMMMMMMMMMMMM")

                        if res["status"] and not res["requery"]:
                            # print("SUUCCEESSSS NOT REQUEEERYY")
                            response_data = {
                                "status": True,
                                "data": "Airtime successfully recharged",
                                "code": "SUCCESS",
                            }

                            track_user_activity.delay(
                                action="airtime purchase succeeds",
                                actor_email=request.user.email,
                            )
                            update_transaction_status.delay(
                                transaction_id, "success", dict_data
                            )
                            NotificationManager.fcm_notification_task(
                                title="Airtime Purchase",
                                body=f"Airtime recharge of NGN {format_currency(amount)} was successful",
                                reciever_email=user.email,
                            )

                            # send email notification
                            send_email_notification_async.delay(
                                "airtime-purchase.html",
                                " Airtime Purchase",
                                recipients=[user.email],
                                context={
                                    "first_name": user.first_name,
                                    "network_provider": service_type,
                                    "phone_number": phone,
                                    "amount": format_currency(amount),
                                },
                            )

                            # track profit transaction
                            from Transactions.models import TransactionModel

                            txn_model = TransactionModel.objects.get(
                                id=transaction_id
                            )

                            if service_type == "mtn":
                                create_profit_transaction.delay(
                                    category="AIRTIME_PAYMENT",
                                    transaction_type="Credit",
                                    reference=txn_model.reference,
                                    amount=(2 / 100) * amount,  # in naira
                                    status="2",
                                    user=request.user.id,
                                    wallet=wallet_balance.id,
                                    transaction_id=transaction_id,
                                )

                            elif service_type == "airtel":
                                create_profit_transaction.delay(
                                    category="AIRTIME_PAYMENT",
                                    transaction_type="Credit",
                                    reference=txn_model.reference,
                                    amount=(2 / 100) * amount,  # in naira
                                    status="2",
                                    user=request.user.id,
                                    wallet=wallet_balance.id,
                                    transaction_id=transaction_id,

                                )

                            elif service_type == "9mobile":
                                create_profit_transaction.delay(
                                    category="AIRTIME_PAYMENT",
                                    transaction_type="Credit",
                                    reference=txn_model.reference,
                                    amount=(3.5 / 100) * amount,  # in naira
                                    status="2",
                                    user=request.user.id,
                                    wallet=wallet_balance.id,
                                    transaction_id=transaction_id,

                                )

                            elif service_type == "glo":
                                create_profit_transaction.delay(
                                    category="AIRTIME_PAYMENT",
                                    transaction_type="Credit",
                                    reference=txn_model.reference,
                                    amount=(3.5 / 100) * amount,  # in naira
                                    status="2",
                                    user=request.user.id,
                                    wallet=wallet_balance.id,
                                    transaction_id=transaction_id,

                                )

                            return Response(
                                {
                                    "status": True,
                                    "data": "Airtime successfully recharged",
                                },
                                status=status.HTTP_200_OK,
                            )

                        if not res["status"] and not res["requery"]:
                            try:
                                # print("IN TRYYYYY")
                                wallet_object = WalletModel.objects.get(
                                    user_id=user.id, currency=currency
                                )
                            except (
                                    WalletModel.DoesNotExist,
                                    WalletModel.MultipleObjectsReturned,
                            ):
                                # print("IN EXCEPT")
                                # requery_transaction.delay(agent_ref)
                                return Response(
                                    {
                                        "status": False,
                                        "code": "AIRTIME_FAILED",
                                        "message": "refund failed weh have been alerted",
                                    },
                                    status=status.HTTP_417_EXPECTATION_FAILED,
                                )
                            # print("NOT SUUCCEESSSS REQUEEERYY")
                            res_data = {**res, **payment_serializer.data}
                            # res_data = {**res, **dict_data}
                            refund_user_wallet.delay(
                                request.user.id,
                                wallet_object.wallet_id,
                                amount,
                                res["message"],
                                "Airtime",
                                res_data,
                                trans_id=transaction_id,
                            )
                            response_data = {
                                "status": False,
                                "data": json.loads(res["data"]),
                                "error": "AIRTIME_FAILED",
                                "message": "Unable to complete, process cancelled",
                            }
                            # print("IN EXCEPT")
                            # requery_transaction.delay(agent_ref)
                            return Response(
                                response_data,
                                status=status.HTTP_417_EXPECTATION_FAILED,
                            )

                        if not res["status"] and res["requery"]:
                            res_data = {**res, **payment_serializer.data}
                            update_transaction_status.delay(
                                transaction_id, "failed", res_data
                            )
                            return Response(
                                error_code.TRANSACTION_IN_PROGRESS,
                                status=status.HTTP_417_EXPECTATION_FAILED,
                            )

                    # here
                    else:
                        # print("UNABLE TO DEBIT WALLET")
                        # Todo: need to reversr transaction here

                        response_data = {
                            "status": False,
                            "data": json.loads(res["data"]),
                            "error": "AIRTIME_FAILED",
                            "message": "Unable to debit wallet, process cancelled",
                        }
                        return Response(
                            response_data,
                            status=status.HTTP_417_EXPECTATION_FAILED,
                        )

            else:
                response_data = {
                    "status": False,
                    "data": payment_serializer.errors,
                    "error": "AIRTIME_FAILED",
                    "message": "Unable to debit wallet, process cancelled",
                }
                return Response(
                    response_data, status=status.HTTP_400_BAD_REQUEST
                )

        except Exception as error:
            transaction.savepoint_rollback(save_point_rollback)
            error_string = "{}".format(error)
            return Response(
                {"error": error_string, "code": "UNKNOWN_ERROR"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def compareBalanceWithServiceAmount(self, balance, service_amount):
        """
        Compare if wallet balance is enough to perform this operation
        """
        if balance < service_amount:
            return False, "Your wallet balance is low"
        return True, ""

    def loadAirtime(self, data, url):
        try:
            header_ = {
                "Authorization": "Api-key " + settings.BAXI_BAP_ACCESS_KEY,
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
            method_ = requests.post
            params_ = {}

            request_airtime_recharge = makeRemoteCall(
                url, data, params_, header_, method_
            )
            to_json_airtime = request_airtime_recharge.json()
            # print(to_json_airtime, "JSOOOOOONNNNN")
            posible_requey_statuses = [
                "BX0001",
                "BX0019",
                "BX0021",
                "BX0024",
                "EXC00103",
                "EXC00105",
                "EXC00109",
                "EXC00114",
                "EXC00124",
                "UNK0001",
                "EXC00001",
            ]

            if (
                    to_json_airtime["status"] == "success"
                    and str(to_json_airtime["code"]) == "200"
            ):
                res = {
                    "status": True,
                    "message": to_json_airtime.get("data").get(
                        "transactionMessage"
                    ),
                    "data": data,
                    "requery": False,
                }
                return res
            elif (
                    to_json_airtime["status"] == "processing"
                    and str(to_json_airtime["code"]) == "200"
            ):
                res = {
                    "status": False,
                    "message": to_json_airtime.get("data").get(
                        "transactionMessage", "purchase Success"
                    ),
                    "data": data,
                    "requery": True,
                }
                return res

            elif str(to_json_airtime["code"]) in posible_requey_statuses:
                res = {
                    "status": False,
                    "message": "Purchase in Process",
                    "data": to_json_airtime.get("data"),
                    "requery": True,
                }
                return res
            elif to_json_airtime["status"] == "error":
                res = {
                    "status": False,
                    "message": to_json_airtime.get("message"),
                    "data": json.dumps(to_json_airtime["errors"]),
                    "requery": False,
                }
                return res
            else:
                res = {
                    "status": False,
                    "message": to_json_airtime.get("message", ""),
                    "data": json.dumps(to_json_airtime["errors"]),
                    "requery": False,
                }
                return res

        except Exception as error:
            error_manager = TeamsErrorManager()
            error_manager.send_error_notification(error)

            error_string = "{}".format(error)
            res = {
                "status": False,
                "message": f"Could not complete request: {error_string}",
                "data": {},
                "requery": False,
            }
            return res