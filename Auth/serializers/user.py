from rest_framework import serializers
from Auth.models.user import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'password', 'name', 'username', 'mobile', 'create_pin', 'package', 'refered_by', 'hearFrom', 'role', 'status', 'created_at', 'updated_at')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create(
            email=validated_data['email'],
            name=validated_data['name'],
            username=validated_data['username'],
            mobile=validated_data['mobile'],
            create_pin=validated_data['create_pin'],
            package=validated_data['package'],
            refered_by=validated_data.get('refered_by', None),
            hearFrom=validated_data.get('hearFrom', None),
            role=validated_data.get('role', None),
            status=validated_data.get('status', None),
        )
        user.set_password(validated_data['password'])
        user.save()
        return user
