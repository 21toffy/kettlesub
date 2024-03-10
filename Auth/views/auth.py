from rest_framework import status
from rest_framework.response import Response
from django.core.exceptions import ValidationError
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
    TokenBlacklistSerializer
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenBlacklistView
)
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_str, force_str
from rest_framework import status
from rest_framework.views import APIView
from Common.custom_response import custom_response
from Auth.serializers.auth import *
from Auth.utils.user import send_reset_email
import traceback


class LoginView(TokenObtainPairView):
    """
    API endpoint for user login.

        - Authenticates user credentials and provides JWT tokens

    Handles POST requests for user login.

        Args:
             request: The HTTP request object.

        Returns:
             Response: JSON response indicating the status of the login process

    """
    serializer_class = TokenObtainPairSerializer

    def post(self, request, **kwargs):
        try:
            serializer = UserAuthenticationSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data

            email = validated_data["email"]
            password = validated_data["password"]

            user = authenticate(request, username=email, password=password)

            if user is not None:
                tokens = super().post(request)
                data = {"email": user.email, "fullname": user.name}

                return Response({
                    "data": data,
                    "message": "Logged in successfully",
                    "status_code": status.HTTP_200_OK,
                    "status_text": "success",
                    "tokens": tokens.data
                })
            else:
                return Response({
                    "data": None,
                    "message": "Invalid credentials",
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "status_text": "error"
                })
        except Exception as e:
            error_message = f"An error occurred while logging in: {str(e)}"
            return Response({
                "data": None,
                "message": error_message,
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status_text": "error"
            })


class RefreshTokenView(TokenRefreshView):
    """
    API endpoint for refreshing JWT tokens.

        - Allows users to refresh their expired access tokens.

    Handles POST requests for refreshing JWT tokens.

        Args:
            request: The HTTP request object.

        Returns:
            Response: JSON response indicating the status of the token refresh process.

    """
    serializer_class = TokenRefreshSerializer

    def post(self, request, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        access_token = validated_data.get('access')
        return Response({
            "message": "Refreshed successfully",
            "token": access_token,
            "status": "success"
        }, status=status.HTTP_200_OK)


class Logout(TokenBlacklistView):
    """
    API endpoint for user registration

        - Blacklists the user's JWT token upon logout.

    Handles POST requests for user logout.

        Args:
            request: The HTTP request object.

        Returns:
            Response: JSON response indicating the status of the logout process.

    """
    serializer_class = TokenBlacklistSerializer

    def post(self, request, *args, **kwargs):
        print(self, request, *args, **kwargs)
        serializer = self.serializer_class(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            return Response("Logged out successfully", status.HTTP_200_OK)

        except TokenError:
            return Response("Token is blacklisted.", status.HTTP_401_UNAUTHORIZED)


class ForgotPasswordView(APIView):
    """
    API endpoint for initiating the password reset process.

    Handles POST requests for initiating password reset.

    Args:
        request: The HTTP request object.

    Returns:
        Response: JSON response indicating the status of the password reset process.
    """
    serializer_class = ForgotPasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        user = User.objects.filter(email=email).first()
        if user:
            try:
                reset_token = PasswordResetTokenGenerator().make_token(user)
                reset_link = self._get_reset_link(request, user, reset_token)

                print(f"Reset link generated: {reset_link}")

                send_reset_email(email, reset_link.encode('utf-8'))

                return Response({'message': 'Password reset email sent successfully.'}, status.HTTP_200_OK)
            except Exception as e:
                return Response({'message': 'Error sending reset email.', 'error': str(e)},
                                status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({'message': 'No user found with the provided email.'}, status.HTTP_404_NOT_FOUND)

    def _get_reset_link(self, request, user, reset_token):
        uidb64 = urlsafe_base64_encode(smart_str(user.id))
        reset_link = request.build_absolute_uri(
            f'/reset-password/{uidb64}/{reset_token}/'
        )
        return reset_link


class ResetPasswordView(APIView):
    """
    API endpoint for resetting the user password.

    Handles POST requests for resetting the password.

    Args:
        request: The HTTP request object.

    Returns:
        Response: JSON response indicating the status of the password reset process.
    """
    serializer_class = ResetPasswordSerializer

    def post(self, request, uidb64, token, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = self._get_user(uidb64)
        if user and PasswordResetTokenGenerator().check_token(user, token):
            try:
                user.set_password(serializer.validated_data['new_password'])
                user.save()
                return Response({'message': 'Password reset successful.'}, status.HTTP_200_OK)
            except ValidationError as e:
                return Response({'message': 'Error resetting password.', 'error': str(e)},
                                status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({'message': 'Invalid reset link.'}, status.HTTP_400_BAD_REQUEST)

    def _get_user(self, uidb64):
        try:
            user_id = force_str(urlsafe_base64_decode(uidb64))
            return User.objects.get(id=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return None
