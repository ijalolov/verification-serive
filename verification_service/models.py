from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils.crypto import get_random_string
from django.db.models import F
from typing import Tuple
from phonenumber_field.modelfields import PhoneNumberField
from uuid import uuid4

from verification_service.utils import get_ip_address



class BaseVerification(models.Model):
    """"""
    
    scope = None
    default_expire_timedelta = 2 * 60  # seconds
    default_allowed_attempts = 3
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    ip = models.CharField(null=True, blank=True, max_length=255)

    code = models.CharField(max_length=255)
    attempts = models.PositiveSmallIntegerField(default=0)
    expired_at = models.DateTimeField()
    verified = models.BooleanField(default=False)
    active = models.BooleanField(default=True)

    verification_state = models.CharField(max_length=128)

    class Meta:
        abstract = True

    def send_code(self) -> bool:
        """
        message = "Your code: %(code)s"
        example:
            message % {'code': 125432} => Your code: 125432
        """
        
        pass  
    
    @classmethod
    def get_instance(cls, request, **kwargs):
        instance = cls(
            code=cls.get_random_code(),
            verification_state=cls.get_random_state(),
            ip=get_ip_address(request),
            **kwargs
        )
        return instance

    @classmethod
    def check_code(cls, state, code) -> Tuple[bool, str]:
        """check is code correct"""
        try:
            ins = cls.objects.get(verification_state=state, verified=False, active=True)
        except cls.DoesNotExist:
            return False, _("State not found.")
        if ins.expired_at < timezone.now():
            success = False
            ins.active = True
            ins.save(update_fields=('active',))
            message = _("Time expired.")
        elif ins.attempts >= cls.get_allowed_attempts_count():
            success = False
            ins.active = True
            ins.save(update_fields=('active',))
            message = _("All attempts are used.")
        elif ins.code != code:
            success = False
            message = _("Invalid code.")
            ins.attempts = F('attempts') + 1
            ins.save(update_fields=('attempts',))
        else:
            success = True
            message = _("Verified.")
            ins.attempts = F('attempts') + 1
            ins.verified = True
            ins.save(update_fields=('attempts', 'verified'))
        return success, message
    
    def make_used(self):
        if self.verified and self.active:
            self.active = False
            self.save(update_fields=('active',))
            

    @classmethod
    def get_message_pattern(cls):
        return settings.VERIFICATION_SERVICE[cls.scope]['message_pattern']
        
    @classmethod
    def get_expire_timedelta(cls):
        seconds = settings.VERIFICATION_SERVICE[cls.scope]['expire_timedelta']
        return timedelta(seconds=seconds)

    @classmethod
    def get_random_code(cls, length=6, allow_chars="0123456789") -> str:
        return get_random_string(length, allow_chars)

    @classmethod
    def get_random_state(cls) -> str:
        return uuid4().hex

    @classmethod
    def get_allowed_attempts_count(cls):
        return settings.VERIFICATION_SERVICE[cls.scope]['allowed_attempts']


class SMSVerification(BaseVerification):
    scope = 'sms'
    phone_number = PhoneNumberField(verbose_name=_('Phone number'))

    def send_code(self) -> bool:
        expire_seconds = settings.VERIFICATION_SERVICE[self.scope]['code_expire']
        self.expired_at = timezone.now() + timedelta(seconds=expire_seconds)
        message_pattern = self.get_message_pattern()
        message = message_pattern % {'code': self.code}
        print('Sent sms...')
        print(message)
        return True

    class Meta:
        db_table = 'verification_service_sms'
        verbose_name = _("SMS Verification")
        verbose_name_plural = _("SMS Verifications")
        ordering = ('-id',)


class EmailVerification(BaseVerification):
    scope = 'email'
    email = models.EmailField(max_length=128)

    def send_code(self) -> bool:
        expire_seconds = settings.VERIFICATION_SERVICE[self.scope]['code_expire']
        self.expired_at = timezone.now() + timedelta(seconds=expire_seconds)
        message_pattern = self.get_message_pattern()
        message = message_pattern % {'code': self.code}
        print('Sent email...')
        print(message)
        return True

    class Meta:
        db_table = 'verification_service_email'
        verbose_name = _("Email Verification")
        verbose_name_plural = _("Email Verifications")
