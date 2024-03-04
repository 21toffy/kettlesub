from django.core.exceptions import ObjectDoesNotExist
from rest_framework.permissions import IsAuthenticated
from Wallet.views.serializers import *
from rest_framework import status
from rest_framework.views import APIView
from Common.custom_response import custom_response
from django.db import transaction
from Common.utils.wallet_operation import debit_credit_user_wallet


class SetPin(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PinSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return custom_response(data=None, message=str(e), status_code=status.HTTP_400_BAD_REQUEST,
                                   status_body="error")

        pin = serializer.validated_data['pin']
        user = request.user

        try:
            user.pin = pin
            user.save()
            return custom_response(data=None, message='PIN set successfully', status_code=status.HTTP_200_OK,
                                   status_body="success")
        except Exception as e:
            return custom_response(data=None, message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                   status_body="error")


class GetWalletBalanceView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = GetWalletBalanceSerializer

    def get(self, request, *args, **kwargs):
        user = request.user
        try:
            main_wallet = Wallet.objects.get(user=user, wallet_type='MAIN')
            bonus_wallet = Wallet.objects.get(user=user, wallet_type='BONUS')
        except Wallet.DoesNotExist:
            return custom_response(data=None, message='Wallet not found for the user',
                                   status_code=status.HTTP_404_NOT_FOUND, status_body="error")

        serializer = self.serializer_class({
            'get_main_wallet': main_wallet,
            'get_bonus_wallet': bonus_wallet
        })

        return custom_response(data=serializer.data, message='Wallet balances retrieved successfully',
                               status_code=status.HTTP_200_OK, status_body="success")


class WalletTransferView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_classes = WalletModelSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_classes(data=request.data)
        if serializer.is_valid():
            wallet_transfer_data = serializer.validated_data

            try:
                with transaction.atomic():
                    sender_wallet = Wallet.objects.gets(
                        id=wallet_transfer_data['sender_wallet_id'],
                        user__username=wallet_transfer_data['sender_username'],
                        wallet_type=wallet_transfer_data['wallet_type']
                    )

                    receiver_wallet = Wallet.objects.get(
                        id=wallet_transfer_data['receiver_wallet_id'],
                        user__username=wallet_transfer_data['receiver_username'],
                        wallet_type=wallet_transfer_data['wallet_type']
                    )

                    # Check if receiver wallet is none
                    if receiver_wallet is None:
                        return custom_response(
                            data=None,
                            message='Receiver wallet not found',
                            status_code=status.HTTP_404_NOT_FOUND,
                            status_body="error"
                        )

                    # Check if sender has enough balance
                    if sender_wallet.balance < wallet_transfer_data['amount']:
                        return custom_response(
                            data=None,
                            message='Insufficient balance in sender wallet',
                            status_code=status.HTTP_400_BAD_REQUEST,
                            status_body="error"
                        )
                    # check PIN
                    if sender_wallet.user.pin != wallet_transfer_data['pin']:
                        return custom_response(
                            data=None,
                            message='Incorrect PIN',
                            status_code=status.HTTP_400_BAD_REQUEST,
                            status_body="error"
                        )
                    # Perform the first wallet operation (debit)
                    success, error_message, txn_id = debit_credit_user_wallet(
                        user=sender_wallet.user,
                        wallet_type=wallet_transfer_data['wallet_type'],
                        amount=wallet_transfer_data['amount'],
                        ref=wallet_transfer_data['ref'],
                        wallet_id=wallet_transfer_data['wallet_id'],
                        action="debit",
                        description="Wallet Transfer",
                    )
                    if not success:
                        raise Exception(error_message)

                    success, error_message, _ = debit_credit_user_wallet(
                        user=receiver_wallet.user,
                        wallet_type=wallet_transfer_data['wallet_type'],
                        amount=wallet_transfer_data['amount'],
                        ref=wallet_transfer_data['ref'],
                        wallet_id=receiver_wallet.id,
                        action="credit",
                        description="Wallet Transfer",
                        transaction_context={'sender_txn_id': txn_id}
                    )

                    if not success:
                        raise Exception(error_message)

                    return custom_response(
                        data={'message': f'{wallet_transfer_data["wallet_type"]} wallet transfer successful'},
                        message='Wallet transfer successful',
                        status_code=status.HTTP_200_OK,
                        status_body="success"
                    )

            except ObjectDoesNotExist as e:
                return custom_response(
                    data=None,
                    message=str(e),
                    status_code=status.HTTP_404_NOT_FOUND,
                    status_body="error"
                )

            except Exception as e:
                print(f"An error occurred: {e}")

                return custom_response(
                    data=None,
                    message='Internal Server Error',
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    status_body="error"
                )
            else:
                return custom_response(
                    data=None,
                    message='Invalid data',
                    status_code=status.HTTP_400_BAD_REQUEST,
                    status_body="error"
                )
