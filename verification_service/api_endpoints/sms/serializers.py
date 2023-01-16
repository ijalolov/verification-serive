from django.core.validators import RegexValidator
from rest_framework import serializers


class SMSSendCodeSerializer(serializers.Serializer):  # noqa
    phone_number = serializers.CharField(max_length=15, required=True, validators=[
        RegexValidator(
            regex=r'^\+1?\d{9,15}$',
            message="Phone number must be entered in the format: '+999999999'. Up to 20 digits allowed."
        )
    ])


class SMSCheckCodeSerializer(serializers.Serializer):  # noqa
    uuid = serializers.CharField(max_length=64, required=True)
    code = serializers.CharField(max_length=6, required=True)
