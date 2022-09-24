from rest_framework import serializers
from .models import SMSVerification
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from .utils import get_ip_address



class SMSVerificationCreateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = SMSVerification
        fields = ('phone_number', 'verification_state')
        read_only_fields = ('verification_state',)
    
    def validate(self, attrs):
        attrs = super().validate(attrs)
        phone_number = attrs['phone_number']
        sms_confirmation = SMSVerification.objects.filter(phone_number=phone_number).order_by('-id').first()
        if sms_confirmation:
            if (
                sms_confirmation.created_at >
                timezone.now() - timedelta(seconds=settings.VERIFICATION_SERVICE[SMSVerification.scope]['sms_min_period'])
            ):
                delta = (
                    sms_confirmation.created_at - timezone.now() +
                    timedelta(seconds=settings.VERIFICATION_SERVICE[SMSVerification.scope]['sms_min_period'])
                ).seconds
                raise serializers.ValidationError(_('Try after %(seconds)s') % {'seconds': delta})
        return attrs
    
    def save(self):
        instance = SMSVerification.get_instance(
            request=self.context['request'], 
            phone_number=self.validated_data['phone_number']
        )
        instance.send_code()
        instance.save()
        self.instance = instance
        return instance


class SMSVerifySerializer(serializers.ModelSerializer):
    
    class Meta:
        model = SMSVerification
        fields = ('phone_number', 'verification_state', 'code')
    
    def validate(self, attrs):
        attrs = super().validate(attrs)
        success, message = SMSVerification.check_code(attrs['verification_state'], attrs['code'])
        if not success:
            raise serializers.ValidationError({'code': message})
        return attrs        
