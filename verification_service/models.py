from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils.crypto import get_random_string
from typing import Tuple
from phonenumber_field.modelfields import PhoneNumberField
from uuid import uuid4

from rest_framework import serializers

from verification_service.utils import get_ip_address


class BaseVerification(models.Model):
    
    scope = None

    created_at = models.DateTimeField(auto_now_add=True)
    ip = models.CharField(null=True, blank=True, max_length=255)

    code = models.CharField(max_length=255)
    attempts = models.PositiveSmallIntegerField(default=0)
    expired_at = models.DateTimeField()
    verified = models.BooleanField(default=False)
    code_sent_successfully = models.BooleanField(default=False)

    signature = models.CharField(max_length=128)

    class Meta:
        abstract = True

    def _send_code(self):
        expire_seconds = SMSVerification.get_expire_timedelta()
        self.expired_at = timezone.now() + timedelta(seconds=expire_seconds)
        message_pattern = self.get_message_pattern()
        message = message_pattern % {'code': self.code}
        pass

    def send_code(self) -> bool:
        raise NotImplementedError

    @classmethod
    def check_code(cls, state, code) -> Tuple[bool, bool, str, str]:
        """check is code correct"""
        try:
            ins = cls.objects.get(verification_state=state, verified=False)
        except cls.DoesNotExist:
            return False, False, 'confirmation_state_not_found', _("State not found.")
        delete_ins = False
        if ins.expired_at < timezone.now():
            success = False
            delete_ins = True
            message_code = 'confirmation_code_expired'
            message = _("Time expired.")
        elif ins.attempts >= cls.get_allowed_attempts_count():
            success = False
            delete_ins = True
            message_code = 'confirmation_not_attempt_left'
            message = _("All attempts are used.")
        elif ins.code != code:
            success = False
            message_code = 'confirmation_code_incorrect'
            message = _("Invalid code.")
            ins.attempts += 1
            if ins.attempts >= cls.get_allowed_attempts_count():
                delete_ins = True
                message_code = 'confirmation_not_attempt_left'
                message = _("All attempts are used.")
            else:
                ins.save(update_fields=('attempts',))
        else:
            success = True
            message_code = 'confirmation_code_verified'
            message = _("Verified.")
            ins.verified = True
            ins.save(update_fields=('attempts', 'verified', 'active'))
        return success, delete_ins, message_code, message
    
    def make_used(self):
        if self.id and self.verified and self.expired_at > timezone.now():
            self.delete()

    @classmethod
    def get_default_settings(cls):
        return {
            'message_pattern': 'Your code: %(code)s',
            'expire_timedelta': 2 * 60,  # 2 minutes
            'allowed_attempts': 3,
            'allowed_characters': '0123456789',
            'code_length': 6,
            'throttle': (1, timedelta(seconds=1)),  # max 10 times per day
        }

    @classmethod
    def settings(cls) -> dict:
        service_settings = getattr(settings, 'VERIFICATION_SERVICE', dict())
        service_settings = service_settings.get(cls.scope, dict())
        return {**cls.get_default_settings(), **service_settings}

    @classmethod
    def get_random_code(cls) -> str:
        setts = cls.settings()
        return get_random_string(setts['code_length'], setts['allowed_characters'])

    @classmethod
    def get_signature(cls) -> str:
        return uuid4().hex


class SMSVerification(BaseVerification):
    scope = 'sms'
    phone_number = PhoneNumberField(verbose_name=_('Phone number'))

    def send_code(self):
        print('send_code', self.phone_number, self.code)

    @classmethod
    def check_throttle(cls, phone_number, request, setts):
        count, period = setts['throttle']
        if cls.objects.filter(
            phone_number=phone_number,
            created_at__gte=timezone.now() - period,
        ).count() >= count:
            raise serializers.ValidationError({'phone_number': 'Throttled'}, code='throttled')

    @classmethod
    def check_for_create(cls, phone_number, request):
        setts = cls.settings()
        validators = ('check_throttle', )
        for validator in validators:
            getattr(cls, validator)(phone_number, request, setts)

    @classmethod
    def create_instance(cls, phone_number, request):
        setts = cls.settings()
        instance = cls.objects.create(
            phone_number=phone_number,
            code=get_random_string(setts['code_length'], setts['allowed_characters']),
            signature=cls.get_signature(),
            expired_at=timezone.now() + timedelta(seconds=setts['expire_timedelta']),
            ip=get_ip_address(request),
        )
        instance.send_code()
        instance.code_sent_successfully = True
        instance.save(update_fields=('code_sent_successfully',))
        return instance

    class Meta:
        db_table = 'verification_service_sms'
        verbose_name = _("SMS Verification")
        verbose_name_plural = _("SMS Verifications")
        ordering = ('-id',)


class EmailVerification(BaseVerification):
    scope = 'email'
    email = models.EmailField(max_length=1024, verbose_name=_('Email'))

    class Meta:
        db_table = 'verification_service_email'
        verbose_name = _("Email Verification")
        verbose_name_plural = _("Email Verifications")
