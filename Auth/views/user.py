from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.db import IntegrityError
from Auth.serializers import UserRegistrationSerializer
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
    serializer_class = UserRegistrationSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        password = validated_data.pop('password', None)

        try:
            user = User.objects.create_user(
                email=validated_data['email'],
                password=password,
                name=validated_data['name'],
                username=validated_data['username'],
                mobile=validated_data['mobile'],
                create_pin=validated_data['create_pin'],
                package=validated_data['package'],
                refered_by=validated_data.get('refered_by'),
                hearFrom=validated_data.get('hearFrom'),
                role=validated_data.get('role'),
                status=validated_data.get('status'),
            )

            return Response({"message": "User created successfully"}, status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response({"message": "An error occurred during user creation"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


