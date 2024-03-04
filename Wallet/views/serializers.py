from abc import ABC
from rest_framework import serializers
from Wallet.models.wallet import Wallet
from Auth.models.user import User


class PinValidator:
    def __call__(self, value):
        if not value.isdigit() or len(value) != 4:
            raise serializers.ValidationError("PIN must be a 4-digit numeric value.")


class WalletModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['id', 'user', 'balance', 'currency', 'wallet_type']


class PinSerializer(serializers.Serializer):
    pin = serializers.CharField(max_length=4, validators=[PinValidator()])

    def validate_pin(self, value):
        if not self.is_pin_valid(value):
            raise serializers.ValidationError("Invalid PIN. Please enter a valid PIN.")
        user_model = User
        user = user_model.objects.filter(pin=value).first()
        if not user:
            raise serializers.ValidationError("PIN is not associated with any user.")

        return value

    def is_pin_valid(self, pin):
        return len(pin) == 4 and pin.isdigit()


class GetWalletBalanceSerializer(serializers.Serializer):
    main_wallet = WalletModelSerializer(source='get_main_wallet', read_only=True)
    bonus_wallet = WalletModelSerializer(source='get_bonus_wallet', read_only=True)
