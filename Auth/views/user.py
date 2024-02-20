from Common.custom_response import custom_response
from rest_framework.views import APIView
from rest_framework import status
from Auth.utils.user import generate_otp, send_otp_email
from django.db import IntegrityError
from Auth.serializers import RegisterSerializer, OTPVerificationSerializer, OTPSerializer
from Auth.models import User


class RegistrationView(APIView):
    """
    API endpoint for user registration.

        - Receives user registration data.

        - Creates a new user, generates a verification code, and sends and sends an email for verification.

    Handles POST requests for user registration

        Args:
            :Request: The HTTP request object.

        Returns:
            Response: JSON response indicating the status of the user creation process.

    """
    serializer_class = RegisterSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        password = validated_data.pop('password', None)
        try:
            user = User.objects.create_user(email=validated_data['email'],
                                     password=password)
            otp_serializer = OTPSerializer(data={'email': validated_data['email']})
            otp_serializer.is_valid(raise_exception=True)

            otp_code = generate_otp(user)
            send_otp_email(user, otp_code)

            return custom_response({"message": "User created successfully"},
                                   status.HTTP_201_CREATED, "success")
        except IntegrityError:
            return custom_response({"message": "An error occurred during user creation"},
                                   status.HTTP_500_INTERNAL_SERVER_ERROR, 'failed')


class VerificationView(APIView):
    """
    API endpoint for OTP verification during user registration.

        - Receives user email and OTP code.

        - Verifies the OTP code.

    Handles POST requests for OTP verification.

        Args:
            :Request: The HTTP request object.

        Returns:
            Response: JSON response indicating the status of the OTP verification process.

    """
    serializer_class = OTPVerificationSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data

        is_valid_otp = self.verify_otp(validated_data['email'], validated_data['otp_code'])

        if is_valid_otp:
            user = User.objects.get(email=validated_data['email'])
            user.is_active = True
            user.save()

    @staticmethod
    def verify_otp(email, otp_code):
        try:
            user = User.objects.get(email=email)
            stored_otp = generate_otp(user)
            return otp_code == stored_otp
        except User.DoesNotExist:
            return False
