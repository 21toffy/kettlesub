import uuid
import json
import requests
from django.conf import settings

from rest_framework.views import APIView
from Merchant.serializers import *  # noqa: F403
from django.conf import settings
from Ups.util.remote import makeRemoteCall
from rest_framework.response import Response
from rest_framework import status, permissions

from Billpayment.serializers import (
    DataBundleProviderSerializer,
    DataBundleBillPaymentSerializer,
)
from Notification.tasks import (
    track_user_activity,
    send_email_notification_async,
)

from django.db import transaction
from Wallet.utils.wallet import WalletUtilities
from Notification.utils.notification_utils import NotificationManager

from datetime import date
from Billpayment.views.id_verification import verify_id
from helpers.baxi_helpers import mocked_transactions, extract_data_from_baxi
from Transactions.tasks import (
    update_transaction_status,
    create_profit_transaction,
    refund_user_wallet,
)
from Wallet.models import WalletModel
import idpaybackendengine.error_code as error_code
from helpers.money import format_currency
from helpers.error_webhooks import TeamsErrorManager, GatewayException
from common.mixins.service_providers import GovaMixin, BaxiMixin


class ListDataBundleServiceProviders(BaxiMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # providers = DataBundleProviders.objects.all().order_by("-created_at").first()
        # serializer = DataBundleServiceProviderSerializer(providers)
        # return Response(serializer.data, status=status.HTTP_200_OK)
        return self.getBaxiDataBunduleProviders()

    def getBaxiDataBunduleProviders(self):
        try:
            url = f"{settings.BAXI_BASE_URL}services/databundle/providers"
            post_data = {}
            params = {}
            header = {
                "Authorization": "Api-key " + settings.BAXI_BAP_ACCESS_KEY,
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
            method = requests.get

            data_providers = makeRemoteCall(
                url, post_data, params, header, method
            )
            to_json = data_providers.json()
            print(to_json["message"])

            if to_json["status"] == "success" and to_json["code"] == 200:
                response_data = to_json["data"]
                response_data = {
                    "status": True,
                    "data": response_data,
                    "code": "SUCCESS",
                }
                return Response(response_data, status=status.HTTP_200_OK)

            else:
                return Response(
                    to_json["message"], status=status.HTTP_400_BAD_REQUEST
                )

                # return False, json.dumps(data_providers["errors"])

        except Exception as error:
            error_string = "{}".format(error)
            print("error_string")
            print(error_string)
            # return False, "Could not complete request"
            return Response(
                error_string, status=status.HTTP_417_EXPECTATION_FAILED
            )


class ListAvailableDataBundleFromSP(BaxiMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        response_data = ""
        today = date.today()
        validator = DataBundleProviderSerializer(data=request.data)

        try:
            if validator.is_valid():
                service_type = validator.data.get("service_type")
                account_number = validator.data.get("account_number")
                url = f"{settings.BAXI_BASE_URL}services/databundle/bundles"
                post_data = {
                    "service_type": service_type,
                    "account_number": account_number,
                }
                params = {}
                header = {
                    "Authorization": "Api-key " + settings.BAXI_BAP_ACCESS_KEY,
                    "Baxi-date": today.strftime("%Y/%m/%d"),
                }
                method = requests.post
                # print("before printing available databundles from SP")
                # print(post_data)
                bundle_providers = makeRemoteCall(
                    url, post_data, params, header, method
                )

                to_json = bundle_providers.json()
                # print(to_json, "response")

                if to_json["status"] == "success" and to_json["code"] == 200:
                    response_data = to_json["data"]
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
                        "code": "DATA_FAILED",
                    }
                    return Response(
                        response_data,
                        status=status.HTTP_417_EXPECTATION_FAILED,
                    )
            else:
                response_data = {
                    "status": False,
                    "data": validator.errors,
                    "code": "BAD_REQUEST",
                }
                return Response(
                    response_data, status=status.HTTP_400_BAD_REQUEST
                )

        except (Exception, ValueError, TypeError) as error:
            error_string = "{}".format(error)
            print(error_string)
            response_data = {
                "status": False,
                "data": error_string,
                "code": "UNKNOWN_ERROR",
            }
            return Response(
                response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MakeDataBundleBillPayment(GovaMixin, BaxiMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        dt_serializer = DataBundleBillPaymentSerializer(data=request.data)
        currency = "NGN"
        transfer_type = "BILL_PAYMENT"
        save_point_rollback = ""
        try:
            plan = "prepaid"
            response_data = {}
            agent_id = settings.BAXI_AGENT_ID
            user = request.user
            save_point_rollback = ""
            if dt_serializer.is_valid():
                # generate AgentRef and AgentId
                agent_ref_ = "{}".format(uuid.uuid4().int)
                agent_ref = "DT" + agent_ref_[-8:]
                service_type = dt_serializer.data.get("service_type")
                phone = dt_serializer.data.get("phone")
                datacode = dt_serializer.data.get("datacode")
                datacode_price = dt_serializer.data.get("datacode_price")
                package = dt_serializer.data.get("package")

                verification_type = dt_serializer.data.get("verification_type")
                with transaction.atomic():
                    WalletModel.objects.filter(user=request.user, currency="NGN").select_for_update().first()
                    mock = False
                    # check wallet address balance
                    wallet_balance = WalletUtilities.get_single_balance(
                        self, user, 1
                    )

                    (
                        tier_status,
                        tier_response,
                    ) = WalletUtilities.tier_transaction_check(
                        request.user, wallet_balance, datacode_price, transfer_type
                    )
                    if not tier_status:
                        return tier_response

                    if not mock:
                        flag, flag_message = self.compareBalanceWithServiceAmount(
                            float(wallet_balance.balance), float(datacode_price)
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
                            action="data purchase failed",
                            actor_email=request.user.email,
                        )
                        NotificationManager.fcm_notification_task(
                            title="Data Purchase",
                            body="You have a low wallet balance",
                            reciever_email=user.email,
                        )
                        return Response(
                            response_data,
                            status=status.HTTP_417_EXPECTATION_FAILED,
                        )
                    else:
                        if not mock:
                            verify_flag, verify_message = verify_id(
                                verification_type=verification_type,
                                verification_value=dt_serializer.data.get(
                                    "verification_value"
                                ),
                                user=request.user,
                                device_id=dt_serializer.data["device_id"],
                            )
                        else:
                            # verify_flag, verify_message = True, ""
                            verify_flag, verify_message = verify_id(
                                verification_type=verification_type,
                                verification_value=dt_serializer.data.get(
                                    "verification_value"
                                ),
                                user=request.user,
                                device_id=dt_serializer.data["device_id"],
                            )

                        if not verify_flag:
                            return Response(
                                {
                                    "status": False,
                                    "errors": "DATA_BUNDLE_FAILED",
                                    "details": verify_message,
                                },
                                status=status.HTTP_417_EXPECTATION_FAILED,
                            )
                        # process to make service and debit user wallet
                        data = json.dumps(
                            {
                                "agentReference": agent_ref,
                                "agentId": agent_id,
                                "datacode": datacode,
                                "amount": datacode_price,
                                "service_type": service_type,
                                "phone": phone,
                                "package": package,
                            }
                        )
                        dict_data = {
                            "agentReference": agent_ref,
                            "agentId": agent_id,
                            "datacode": datacode,
                            "amount": datacode_price,
                            "service_type": service_type,
                            "phone": phone,
                            "package": package,
                        }
                        # from Wallet.utils.spending_limit import rate_limiting

                        # print("fffffffffff")
                        # stats, mess = rate_limiting(
                        #     request.user, "Data", datacode_price, datacode, phone
                        # )
                        # print("cccccccc")

                        # if not stats:
                        #     return Response(
                        #         error_code.POSSIBLE_DUPLICATE_TRANSACTION,
                        #         status=status.HTTP_417_EXPECTATION_FAILED,
                        #     )

                        (
                            debit_wallet,
                            save_point_rollback,
                            transaction_id,
                        ) = WalletUtilities.debit_credit_user_wallet(
                            self,
                            user,
                            1,
                            datacode_price,
                            agent_ref,
                            wallet_balance,
                            app="Data",
                            # phone = phone,
                            # datacode = datacode,
                        )
                    print("got here")

                    url = (
                        f"{settings.BAXI_BASE_URL}services/databundle/request"
                    )
                    print("got heree")

                    if debit_wallet:
                        print("got hereee")

                        if not mock:
                            print("got hereee")
                            res = self.loadDataBundle(data, url)
                            print('REQ BODYYYY')
                            print(data)
                            print("RES BODY")
                            print(res)
                            # flg, load_data_response = self.loadDataBundle(data, url)
                        else:
                            import random

                            random_transaction = random.choice(
                                mocked_transactions
                            )
                            res = extract_data_from_baxi(random_transaction)

                        if res["status"] and not res["requery"]:
                            response_data = {
                                "status": True,
                                "data": "Data successfully recharged",
                                "code": "SUCCESS",
                            }

                            update_transaction_status.delay(
                                transaction_id, "success", dict_data
                            )

                            NotificationManager.fcm_notification_task(
                                title="Data Recharge",
                                body="Data recharge was successful",
                                reciever_email=user.email,
                            )

                            # send email notification
                            send_email_notification_async.delay(
                                "data-purchase.html",
                                " Data Purchase",
                                recipients=[user.email],
                                context={
                                    "first_name": user.first_name,
                                    "network_provider": service_type,
                                    "phone_number": phone,
                                    "amount": format_currency(datacode_price),
                                    "data_bundle": "",
                                },
                            )

                            # track profit transaction
                            from Transactions.models import TransactionModel

                            txn_model = TransactionModel.objects.get(
                                id=transaction_id
                            )

                            if service_type == "mtn":
                                create_profit_transaction.delay(
                                    category="DATA_PAYMENT",
                                    transaction_type="Credit",
                                    reference=txn_model.reference,
                                    amount=(2 / 100)
                                           * datacode_price,  # in naira
                                    status="2",
                                    user=request.user.id,
                                    wallet=wallet_balance.id,
                                    transaction_id=transaction_id,

                                )

                            elif service_type == "airtel":
                                create_profit_transaction.delay(
                                    category="DATA_PAYMENT",
                                    transaction_type="Credit",
                                    reference=txn_model.reference,
                                    amount=(2 / 100)
                                           * datacode_price,  # in naira
                                    status="2",
                                    user=request.user.id,
                                    wallet=wallet_balance.id,
                                    transaction_id=transaction_id,

                                )

                            elif service_type == "9mobile":
                                create_profit_transaction.delay(
                                    category="DATA_PAYMENT",
                                    transaction_type="Credit",
                                    reference=txn_model.reference,
                                    amount=(3.5 / 100)
                                           * datacode_price,  # in naira
                                    status="2",
                                    user=request.user.id,
                                    wallet=wallet_balance.id,
                                    transaction_id=transaction_id,

                                )

                            elif service_type == "glo":
                                create_profit_transaction.delay(
                                    category="DATA_PAYMENT",
                                    transaction_type="Credit",
                                    reference=txn_model.reference,
                                    amount=(3.5 / 100)
                                           * datacode_price,  # in naira
                                    status="2",
                                    user=request.user.id,
                                    wallet=wallet_balance.id,
                                    transaction_id=transaction_id,

                                )

                            response_data = {
                                "status": True,
                                "data": "Data recharge was successful",
                                "code": "SUCCESS",
                            }
                            return Response(
                                response_data, status=status.HTTP_200_OK
                            )

                        try:
                            wallet_object = WalletModel.objects.get(
                                user_id=user.id, currency=currency
                            )
                        except (
                                WalletModel.DoesNotExist,
                                WalletModel.MultipleObjectsReturned,
                        ):
                            return Response(
                                {
                                    "status": False,
                                    "code": "DATA_FAILED",
                                    "message": "refund failed weh have been alerted",
                                },
                                status=status.HTTP_417_EXPECTATION_FAILED,
                            )

                        if not res["status"] and not res["requery"]:
                            res_data = {**res, **dt_serializer.data}
                            print("totallllly UGGLY requeryy!!!!!!!!!")
                            refund_user_wallet.delay(
                                request.user.id,
                                wallet_object.wallet_id,
                                datacode_price,
                                res["message"],
                                "DATA",
                                res_data,
                                trans_id=transaction_id,
                            )
                            response_data = {
                                "status": False,
                                "data": json.loads(res["data"]),
                                "error": "DATA_FAILED",
                                "message": "Unable to complete, process cancelled",
                            }
                            # requery_transaction.delay(agent_ref)
                            return Response(
                                response_data,
                                status=status.HTTP_417_EXPECTATION_FAILED,
                            )

                        if not res["status"] and res["requery"]:
                            print("totallllly baddd!!!!!!!!!")
                            res_data = {**res, **dt_serializer.data}
                            update_transaction_status.delay(
                                transaction_id, "failed", res_data
                            )
                            # requery_transaction.delay(agent_ref)
                            return Response(
                                error_code.TRANSACTION_IN_PROGRESS,
                                status=status.HTTP_417_EXPECTATION_FAILED,
                            )

                    else:
                        response_data = {
                            "status": False,
                            "message": save_point_rollback,
                            "code": "DATA_FAILED",
                        }
                        return Response(
                            response_data,
                            status=status.HTTP_417_EXPECTATION_FAILED,
                        )

            else:
                response_data = {
                    "status": False,
                    "data": dt_serializer.errors,
                    "code": "BAD_REQUEST",
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

    def loadDataBundle(self, data, url):
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
            print(to_json_airtime, "JSOOOOOONNNNN")
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