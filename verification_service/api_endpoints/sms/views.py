import datetime
import string
from django.core.cache import cache
from django.utils.crypto import get_random_string
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from . import serializers


SMS_CODE_TIMEOUT = 60 * 60  # 1 hour
SMS_RESEND_TIMEOUT = 60 * 2  # 2 minute
SMS_CODE_MAX_ATTEMPTS = 3  # 3 attempts
SMS_VERIFIED_PHONE_NUMBER_TIMEOUT = 60 * 60 * 2  # 2 hour


class SMSSendCodeView(generics.GenericAPIView):
    serializer_class = serializers.SMSSendCodeSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        uuid = get_random_string(length=32, allowed_chars=string.ascii_letters + string.digits)
        code = get_random_string(length=6, allowed_chars=string.digits)
        old_sends = cache.get_many(cache.keys(f"{serializer.validated_data['phone_number']}_*"))
        now = datetime.datetime.now()
        for old_send in old_sends:
            if (now - old_sends[old_send]['send_at']).total_seconds() < SMS_RESEND_TIMEOUT:
                raise ValidationError({
                    'phone_number': 'sms_code_already_sent'
                }, code='sms_code_already_sent')

        cache.set(
            f"{serializer.valsidated_data['phone_number']}_{uuid}",
            {
                "phone_number": serializer.validated_data['phone_number'],
                "uuid": uuid,
                "code": code,
                "attempts": 0,
                "send_at": datetime.datetime.now(),
                'verified': False
            }, timeout=SMS_CODE_TIMEOUT
        )

        # SEND SMS CODE HERE
        print(f"SMS CODE: {code}")

        return Response(
            {'uuid': uuid},
            status=status.HTTP_200_OK
        )


class SMSCheckCodeView(generics.GenericAPIView):
    serializer_class = serializers.SMSCheckCodeSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cache_data = cache.get_many(cache.keys(f"*_{serializer.validated_data['uuid']}"))
        data = None
        cache_key = None
        for key in cache_data:
            cache_key = key
            data = cache_data[key]
        if data is None or data['verified']:
            raise ValidationError({
                'code': 'sms_invalid_code'
            }, code='sms_invalid_code')

        if data['attempts'] > SMS_CODE_MAX_ATTEMPTS:
            raise ValidationError({
                'code': 'sms_code_expired'
            }, code='sms_code_expired')

        if data['code'] != serializer.validated_data['code']:
            data['attempts'] += 1
            cache.set(cache_key, data, timeout=SMS_CODE_TIMEOUT)
            raise ValidationError({
                'code': 'sms_invalid_code'
            }, code='sms_invalid_code')

        data['verified'] = True
        cache.set(cache_key, data, timeout=SMS_VERIFIED_PHONE_NUMBER_TIMEOUT)

        return Response(
            {'verified': True},
            status=status.HTTP_200_OK
        )
