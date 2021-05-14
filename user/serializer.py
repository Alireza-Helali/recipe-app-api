from django.contrib.auth import get_user_model, authenticate

from rest_framework import serializers


class AuthTokenSerializer(serializers.Serializer):
    """Serializer for user authentication"""
    email = serializers.CharField(max_length=255)
    password = serializers.CharField(
        style={'input_type': 'password',
               }
    )

    def validate(self, attrs):
        """Validate and authenticate the user"""
        email = attrs.get('email')
        password = attrs.get('password')
        user = authenticate(request=self.context.get('request'), username=email, password=password)
        if not user:
            msg = 'Unable to provide the user with provided credentials'
            raise serializers.ValidationError(msg, code='authentication')
        attrs['user'] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    """serializer for user serializer"""

    class Meta:
        model = get_user_model()
        fields = ['email', 'name', 'password']
        extra_kwargs = {
            'password': {'write_only': True, 'min_length': 5,
                         'style': {'input_type': 'password'}, 'trim_whitespace': False
                         },
        }

    def create(self, validated_data):
        """create a new user with encrypted password and return it"""
        return get_user_model().objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user
