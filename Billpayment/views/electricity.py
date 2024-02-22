from rest_framework.views import APIView
from Merchant.serializers import *  # noqa
from django.conf import settings
from Ups.util.remote import makeRemoteCall
from rest_framework.response import Response
import requests
import json
import uuid
from rest_framework import status, permissions
from Billpayment.serializers import (
    ElectricityBillPaymentSerializer,
    DataBundleProviderSerializer,
)
from django.db import transaction
from Wallet.utils.wallet import WalletUtilities
from datetime import date
from Billpayment.models import BillPayment
from Notification.tasks import (
    track_user_activity,
    send_email_notification_async,
)
from Notification.utils.notification_utils import NotificationManager
from Wallet.models import WalletModel
from Billpayment.views.id_verification import verify_id

from Transactions.tasks import (
    update_transaction_status,
    create_profit_transaction,
    refund_user_wallet,
)
from helpers.baxi_helpers import mocked_transactions, extract_data_from_baxi
from helpers.error_webhooks import TeamsErrorManager, GatewayException

import idpaybackendengine.error_code as error_code
from django.conf import settings

from common.mixins.service_providers import GovaMixin, BaxiMixin

from enum import Enum

from Transactions.models import TransactionModel


class RawOutputKeys(Enum):
    TAX_AMOUNT = 'taxAmount'
    COST_OF_UNIT = 'costOfUnit'
    TARIFF = 'tariff'
    EXCHANGE_REFERENCE = 'exchangeReference'


class ListElectricityServiceProviders(BaxiMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            url = f"{settings.BAXI_BASE_URL}services/electricity/billers"
            post_data = {}
            params = {}
            header = {
                "Authorization": "Api-key " + settings.BAXI_BAP_ACCESS_KEY,
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
            method = requests.get

            electricity_providers = makeRemoteCall(
                url, post_data, params, header, method
            )
            to_json = electricity_providers.json()

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
                    "code": "ELECTRICITY_FAILED",
                }
                return Response(
                    response_data, status=status.HTTP_417_EXPECTATION_FAILED
                )
        except Exception as error:
            error_string = "{}".format(error)
            response_data = {
                "status": False,
                "data": error_string,
                "code": "UNKNOWN_ERROR",
            }
            return Response(
                response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ElectricityNameFinderQuery(BaxiMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        response_data = ""
        validator = DataBundleProviderSerializer(data=request.data)

        try:
            if validator.is_valid():
                service_type = validator.data.get("service_type")
                account_number = validator.data.get("account_number")
                url = f"{settings.BAXI_BASE_URL}services/namefinder/query"
                post_data = {
                    "service_type": service_type,
                    "account_number": account_number,
                }
                params = {}
                header = {
                    "Authorization": "Api-key " + settings.BAXI_BAP_ACCESS_KEY
                }
                print("URL", url)
                print("BODY", post_data)
                print("HEADER", header)
                method = requests.post

                meter_information = makeRemoteCall(
                    url, post_data, params, header, method
                )
                print(meter_information)
                to_json = meter_information.json()
                print(to_json)

                if to_json["status"] == "success" and to_json["code"] == 200:
                    print(11111)
                    response_data = to_json["data"]
                    response_data = {
                        "status": True,
                        "data": response_data,
                        "code": "SUCCESS",
                    }
                    return Response(response_data, status=status.HTTP_200_OK)
                else:
                    print("3333333")
                    response_data = {
                        "status": False,
                        "data": to_json["message"],
                        "code": "ELECTRICITY_FAILED",
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
            error_manager = TeamsErrorManager()
            error_manager.send_error_notification(error)
            print(error_string)
            response_data = {
                "status": False,
                "data": error_string,
                "code": "UNKNOWN_ERROR",
            }
            return Response(
                response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MakeElectriciryBillPayment(GovaMixin, BaxiMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]
    blocked = False

    def post(self, request):
        if self.blocked:
            return Response(
                {
                    "status": False,
                    "errors": "ELECTRICITY_FAILED",
                    "details": "something went wrong",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            response_data = {}
            transfer_type = "BILL_PAYMENT"
            agent_id = settings.BAXI_AGENT_ID
            url = f"{settings.BAXI_BASE_URL}services/electricity/request"
            user = request.user
            dt_serializer = ElectricityBillPaymentSerializer(data=request.data)
            currency = "NGN"
            save_point_rollback = ""

            if dt_serializer.is_valid():
                agent_ref_ = "{}".format(uuid.uuid4().int)
                agent_ref = "ET" + agent_ref_[-8:]

                service_type = dt_serializer.data.get("service_type")
                amount = dt_serializer.data.get("amount")
                meter_no = dt_serializer.data.get("meter_number")
                device_id = dt_serializer.data["device_id"]
                verification_type = dt_serializer.data.get("verification_type")
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
                            int(wallet_balance.balance), int(amount)
                        )
                    else:
                        # flag, flag_message  = True, "custom tof message Success  "
                        import random

                        result = [
                            [True, "success"],
                            [False, "Your wallet balance is low"],
                        ]
                        selected_item = random.choice(result)
                        flag, flag_message = selected_item[0], selected_item[1]

                    if not flag:
                        return Response(
                            {"status": False, "data": flag_message},
                            status=status.HTTP_417_EXPECTATION_FAILED,
                        )

                    # verify user
                    if not mock:
                        verify_flag, verify_message = verify_id(
                            verification_type=verification_type,
                            verification_value=dt_serializer.data.get(
                                "verification_value"
                            ),
                            user=user,
                            device_id=device_id,
                        )
                    else:
                        verify_flag, verify_message = True, ""

                    if not verify_flag:
                        return Response(
                            error_code.UNABLE_TO_VERIFY_USER,
                            status=status.HTTP_417_EXPECTATION_FAILED,
                        )
                        # check rate limiting
                        from Wallet.utils.spending_limit import rate_limiting

                        stats, mess = rate_limiting(
                            request.user, "Electricity", amount, meter_no=meter_no
                        )
                        if not stats:
                            return Response(
                                error_code.POSSIBLE_DUPLICATE_TRANSACTION,
                                status=status.HTTP_417_EXPECTATION_FAILED,
                            )

                        # process to make service and debit user wallet
                        user_phone = str(request.user.phone)
                        user_phone = (
                            "0" + user_phone[3:]
                            if user_phone[0:3] == "234"
                            else user_phone
                        )

                        data = json.dumps(
                            {
                                "agentReference": agent_ref,
                                "agentId": agent_id,
                                "amount": amount,
                                "account_number": meter_no,
                                "service_type": service_type,
                                "phone": str(user_phone)
                                         or str(request.user.phone_alternate),
                            }
                        )

                        dict_data = {
                            "agentReference": agent_ref,
                            "agentId": agent_id,
                            "amount": amount,
                            "meter_no": meter_no,
                            "service_type": service_type,
                            "phone": user_phone or request.user.phone_alternate,
                        }

                        # debit user account
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
                            app="Electricity",
                            # token=load_data_response,
                            # meter_no = meter_no,
                        )

                    if debit_wallet:
                        if not mock:
                            res = self.rechargeElectricityMeter(data, url, user)
                        else:
                            import random

                            random_transaction = random.choice(mocked_transactions)
                            res = extract_data_from_baxi(random_transaction)

                        if res["status"] and not res["requery"]:
                            load_data_response = res["data"]["data"]["tokenCode"]
                            print("KKKKKKK", res)
                            response_data = {
                                "status": True,
                                "data": f"Electricity Token retrieved : {load_data_response}",
                                "code": "SUCCESS",
                            }
                            track_user_activity.delay(
                                action=f"Electricity Token retrieved : {load_data_response}",
                                actor_email=user.email,
                            )
                            NotificationManager.fcm_notification_task(
                                title="Electricity Purchase",
                                body=f"Electricity token retrieved : {load_data_response}",
                                reciever_email=user.email,
                            )

                            data = res['data']['data']

                            dict_data['statusCode'] = data['statusCode']
                            dict_data['transactionStatus'] = data['transactionStatus']
                            dict_data['transactionReference'] = data['transactionReference']
                            dict_data['tokenCode'] = data['tokenCode']
                            dict_data['tokenAmount'] = data['tokenAmount']
                            dict_data['amountOfPower'] = data['amountOfPower']
                            dict_data['creditToken'] = data['creditToken']
                            dict_data["token"] = load_data_response

                            dict_data['rawOutput'] = None

                            if 'rawOutput' in data:
                                raw_output = data['rawOutput']
                                for key_enum in RawOutputKeys:
                                    key = key_enum.value
                                    dict_data[key] = raw_output.get(key, None)

                            update_transaction_status.delay(
                                transaction_id, "success", dict_data
                            )

                            # send email notification
                            send_email_notification_async.delay(
                                "electricity-purchase.html",
                                " Electricity Purchase",
                                recipients=[user.email],
                                context={
                                    "first_name": user.first_name,
                                    "power_provider": str(service_type).upper(),
                                    "meter_number": meter_no,
                                    "meter_token": load_data_response,
                                },
                            )

                            # track profit transaction

                            txn_model = TransactionModel.objects.get(
                                id=transaction_id
                            )
                            # txn_model.transaction_context = res
                            # txn_model.save()

                            if service_type in [
                                "abuja_electric_postpaid",
                                "abuja_electric_prepaid",
                            ]:
                                create_profit_transaction.delay(
                                    category="ELECTRICITY_BILL",
                                    transaction_type="Credit",
                                    reference=txn_model.reference,
                                    amount=(1.2 / 100) * amount,  # in naira
                                    status="2",
                                    user=request.user.id,
                                    wallet=wallet_balance.id,
                                    transaction_id=transaction_id,

                                )

                            elif service_type in [
                                "ikeja_electric_postpaid",
                                "ikeja_electric_prepaid",
                            ]:
                                create_profit_transaction.delay(
                                    category="ELECTRICITY_BILL",
                                    transaction_type="Credit",
                                    reference=txn_model.reference,
                                    amount=(1 / 100) * amount,  # in naira
                                    status="2",
                                    user=request.user.id,
                                    wallet=wallet_balance.id,
                                    transaction_id=transaction_id,

                                )

                            elif service_type in [
                                "eko_electric_postpaid",
                                "eko_electric_prepaid",
                            ]:
                                create_profit_transaction.delay(
                                    category="ELECTRICITY_BILL",
                                    transaction_type="Credit",
                                    reference=txn_model.reference,
                                    amount=(1 / 100) * amount,  # in naira
                                    status="2",
                                    user=request.user.id,
                                    wallet=wallet_balance.id,
                                    transaction_id=transaction_id,

                                )

                            elif service_type in [
                                "ibadan_electric_prepaid",
                                "ibadan_electric_postpaid",
                            ]:
                                create_profit_transaction.delay(
                                    category="ELECTRICITY_BILL",
                                    transaction_type="Credit",
                                    reference=txn_model.reference,
                                    amount=(0.6 / 100) * amount,  # in naira
                                    status="2",
                                    user=request.user.id,
                                    wallet=wallet_balance.id,
                                    transaction_id=transaction_id,

                                )

                            elif service_type in [
                                "kaduna_electric_prepaid",
                                "kaduna_electric_postpaid",
                            ]:
                                create_profit_transaction.delay(
                                    category="ELECTRICITY_BILL",
                                    transaction_type="Credit",
                                    reference=txn_model.reference,
                                    amount=(1.2 / 100) * amount,  # in naira
                                    status="2",
                                    user=request.user.id,
                                    wallet=wallet_balance.id,
                                    transaction_id=transaction_id,

                                )

                            elif service_type in [
                                "jos_electric_prepaid",
                                "jos_electric_postpaid",
                            ]:
                                create_profit_transaction.delay(
                                    category="ELECTRICITY_BILL",
                                    transaction_type="Credit",
                                    reference=txn_model.reference,
                                    amount=(1 / 100) * amount,  # in naira
                                    status="2",
                                    user=request.user.id,
                                    wallet=wallet_balance.id,
                                    transaction_id=transaction_id,

                                )

                            elif service_type in [
                                "portharcourt_electric_prepaid",
                                "portharcourt_electric_postpaid",
                            ]:
                                create_profit_transaction.delay(
                                    category="ELECTRICITY_BILL",
                                    transaction_type="Credit",
                                    reference=txn_model.reference,
                                    amount=(1.2 / 100) * amount,  # in naira
                                    status="2",
                                    user=request.user.id,
                                    wallet=wallet_balance.id,
                                    transaction_id=transaction_id,

                                )

                            elif service_type in [
                                "kedco_electric_prepaid",
                                "kedco_electric_postpaid",
                            ]:
                                create_profit_transaction.delay(
                                    category="ELECTRICITY_BILL",
                                    transaction_type="Credit",
                                    reference=txn_model.reference,
                                    amount=(1 / 100) * amount,  # in naira
                                    status="2",
                                    user=request.user.id,
                                    wallet=wallet_balance.id,
                                    transaction_id=transaction_id,

                                )

                            return Response(
                                response_data, status=status.HTTP_200_OK
                            )

                        if not res["status"] and not res["requery"]:
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
                                        "code": "AIRTIME_FAILED",
                                        "message": "refund failed weh have been alerted",
                                    },
                                    status=status.HTTP_417_EXPECTATION_FAILED,
                                )
                            print("totallllly UGGLY requeryy!!!!!!!!!")
                            serialized_data = dt_serializer.validated_data
                            res_data = {**res, **serialized_data}
                            refund_user_wallet.delay(
                                request.user.id,
                                wallet_object.wallet_id,
                                amount,
                                res["message"],
                                "Electricity",
                                res_data,
                                trans_id=transaction_id,
                            )

                            response_data = {
                                "status": False,
                                "data": res["data"],
                                "code": "ELECTRICITY_FAILED",
                                "message": "Unable to complete, process cancelled",
                            }
                            # refund cash to wallet here
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
                        # put the code to refund here
                        return Response(
                            {
                                "status": False,
                                "code": "ELECTRICITY_FAILED",
                                "message": save_point_rollback,
                            },
                            status=status.HTTP_417_EXPECTATION_FAILED,
                        )
                else:
                return Response(
                    {"error": dt_serializer.errors, "code": "BAD_REQUEST"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except Exception as error:
            transaction.savepoint_rollback(save_point_rollback)
            error_string = "{}".format(error)
            error_manager = TeamsErrorManager()
            error_manager.send_error_notification(error)
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

    def rechargeElectricityMeter(self, data, url, user_dt):
        try:
            today = date.today()

            header_ = {
                "Authorization": "Api-key " + settings.BAXI_BAP_ACCESS_KEY,
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Baxi-date": today.strftime("%d,%b %Y"),
            }
            method_ = requests.post
            params_ = {}

            request_data_recharge = makeRemoteCall(
                url, data, params_, header_, method_
            )
            to_json_data = request_data_recharge.json()
            # print(f"request_airtime_recharge {request_data_recharge}")
            # print(f"to_json_airtime {to_json_data}")
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

            # if to_json_data["status"] == "success" and to_json_data["code"] == 200:
            if (
                    to_json_data["status"] == "success"
                    and str(to_json_data["code"]) == "200"
            ):
                to_log_with = json.loads(data)

                # log this transaction
                BillPayment.create(
                    {
                        "uid": to_log_with["agentReference"],
                        "amount": to_log_with["amount"],
                        "provider": to_log_with["service_type"],
                        "plan": "no-plan",
                        "bill_gadget_id": to_log_with["account_number"],
                        "response_data": to_json_data,
                        "type_of_bill": "electricity",
                        "user": user_dt,
                    }
                )
                # end of logging
                res = {
                    "status": True,
                    "message": to_json_data.get("data").get(
                        "transactionMessage", to_json_data["message"]
                    ),
                    "data": to_json_data,
                    "requery": False,
                }
                return res
            elif (
                    to_json_data["status"] == "processing"
                    and str(to_json_data["code"]) == "200"
            ):
                res = {
                    "status": False,
                    "message": to_json_data.get("data").get(
                        "transactionMessage", "purchase Success"
                    ),
                    "data": to_json_data["data"],
                    "requery": True,
                }
                return res
            elif str(to_json_data["code"]) in posible_requey_statuses:
                res = {
                    "status": False,
                    "message": "Purchase in Process",
                    "data": to_json_data.get("data"),
                    "requery": True,
                }
                return res
            elif to_json_data["status"] == "error":
                res = {
                    "status": False,
                    "message": to_json_data.get("message"),
                    "data": json.dumps(to_json_data["errors"]),
                    "requery": False,
                }
                return res
            else:
                res = {
                    "status": False,
                    "message": to_json_data.get("message", ""),
                    "data": json.dumps(to_json_data["errors"]),
                    "requery": False,
                }
                return res

        except Exception as error:
            error_string = "{}".format(error)
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

