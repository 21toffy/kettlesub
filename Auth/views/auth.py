from django.contrib.auth import authenticate
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
from rest_framework import status
from Common.custom_response import custom_response
from Auth.serializers.auth import LoginSerializer


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
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        email = validated_data["email"]
        password = validated_data["password"]
        user = authenticate(request, email=email, password=password)

        if user:
            tokens = super().post(request)
            data = {"email": user.email, "fullname": user.fullname}

            return custom_response(
                data=data,
                message="Logged in successfully",
                status_code=status.HTTP_200_OK,
                status_text="success",
                tokens=tokens.data
            )
        else:
            return custom_response(
                data="Invalid credentials",
                message="Invalid credentials",
                status_code=status.HTTP_400_BAD_REQUEST,
                status_text="error"
            )


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
        return custom_response({
            "message": "Refreshed successfully",
            "token": access_token}, status.HTTP_200_OK, "success")


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

        serializer = self.serializer_class(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            return custom_response("Logged out successfully.", status.HTTP_200_OK, "success")
        except TokenError:
            return custom_response("Token is blacklisted.", status.HTTP_400_BAD_REQUEST, "failed")

