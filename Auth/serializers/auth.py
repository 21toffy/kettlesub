from rest_framework import serializers
from Auth.validators.user import validate_email_format


class BaseSerializer(serializers.Serializer):
    def validate_email_format(self, value):
        validate_email_format(value)


class LoginSerializer(BaseSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(max_length=150, min_length=6, write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        self.validate_email_format(email)

        return attrs
