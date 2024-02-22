from pkg_resources import require
from rest_framework import serializers
from Billpayment.models import BillPayment


class BillPaymentSerializer(serializers.Serializer):
    service_type = serializers.CharField(required=True)
    amount = serializers.FloatField(required=True)
    phone = serializers.RegexField(
        regex=r"^[0-9]{11,14}$", required=True, allow_blank=False
    )
    verification_value = serializers.CharField(required=False)
    verification_type = serializers.CharField(required=True)
    device_id = serializers.CharField(required=True)


class ElectricityBillPaymentSerializer(serializers.Serializer):
    service_type = serializers.CharField(required=True)
    amount = serializers.FloatField(required=True)
    meter_number = serializers.CharField(required=True)
    verification_value = serializers.CharField(required=False)
    verification_type = serializers.CharField(required=True)
    device_id = serializers.CharField(required=True)


class DataBundleBillPaymentSerializer(serializers.Serializer):
    service_type = serializers.CharField(required=True)
    phone = serializers.RegexField(
        regex=r"^[0-9]{11,14}$", required=True, allow_blank=False
    )
    datacode = serializers.CharField(required=True)
    datacode_price = serializers.IntegerField(required=True)
    package = serializers.CharField(required=True)
    verification_value = serializers.CharField(required=False)
    verification_type = serializers.CharField(required=True)
    device_id = serializers.CharField(required=True)


class BillPaymentDataSerializer(serializers.ModelSerializer):
    """
    Wallet serializer
    this serializer the data from each wallet record
    """

    class Meta:
        model = BillPayment
        fields = (
            "user",
            "uid",
            "amount",
            "provider",
            "plan",
            "bill_gadget_id",
            "response_data",
            "account_number",
            "type_of_bill",
            "created_at",
        )

    # def to_representation(self, instance):
    #     data = super().to_representation(instance)

    #     if instance.wallet_type == "1":
    #         data['wallet_type'] =  {"id":1,"name":"IDENTITYCASH"}

    #     return data


class DataBundleProviderSerializer(serializers.Serializer):
    service_type = serializers.CharField(required=True)
    account_number = serializers.CharField(required=False)


class DataBundleServiceProviderSerializer(serializers.Serializer):
    providers = serializers.JSONField(read_only=True)


class TelevisionPaymentSerializer(serializers.Serializer):
    SERVICE_TYPE = (
        ("dstv", "dstv"),
        ("gotv", "gotv"),
    )
    smartcard_number = serializers.CharField(required=True)
    total_amount = serializers.IntegerField(required=True)
    product_code = serializers.CharField(required=True)
    product_months_paid_for = serializers.IntegerField(required=True)
    addon_code = serializers.CharField(required=True)
    addon_months_paid_for = serializers.IntegerField(required=True)
    agentId = serializers.IntegerField(required=True)
    service_type = serializers.ChoiceField(choices=SERVICE_TYPE, required=True)
    verification_type = serializers.CharField(required=True)
    verification_value = serializers.CharField(required=False)
    device_id = serializers.CharField(required=True)