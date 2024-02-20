from rest_framework import serializers
from Auth.models.user import User
from Auth.validators.user import validate_email_format, validate_phone_number


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'phone', 'first_name', 'middle_name', 'last_name', 'username', 'referal_code', 'is_admin', 'is_active', 'ussd_pin', 'is_flagged', 'is_frozen']
        extra_kwargs = {
            'password': {'write_only': True, 'min_length': 8},
        }

    def validate_email(self, value):
        validate_email_format(value)
        existing_email = User.objects.filter(email=value)
        if existing_email.exists():
            raise serializers.ValidationError("Email already registered")
        return value

    def validate(self, data):
        first_name = data.get('first_name')
        last_name = data.get('last_name')

        if not first_name or not last_name:
            raise serializers.ValidationError("First name and Last name are required")

        return data

    def validate_phone(self, value):
        validate_phone_number(value)
        return value


class OTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
            return user
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")


class OTPVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_code = serializers.CharField()

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
            return user
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")

    def validate_otp_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("OTP code must be a numeric value.")
        return value

