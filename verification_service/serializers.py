from rest_framework import serializers
from .models import SMSVerification


class SMSVerificationCreateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = SMSVerification
        fields = ('phone_number', 'signature', 'verified')
        read_only_fields = ('signature', 'verified')
    
    def validate(self, attrs):
        attrs = super().validate(attrs)
        SMSVerification.check_for_create(
            phone_number=attrs['phone_number'],
            request=self.context['request']
        )
        return attrs
    
    def save(self):
        instance = SMSVerification.create_instance(
            phone_number=self.validated_data['phone_number'],
            request=self.context['request']
        )
        return instance


class SMSVerifySerializer(serializers.ModelSerializer):
    
    class Meta:
        model = SMSVerification
        fields = ('phone_number', 'signature', 'code')
    
    def validate(self, attrs):
        attrs = super().validate(attrs)
        success, message = SMSVerification.check_code(attrs['signature'], attrs['code'])
        if not success:
            raise serializers.ValidationError({'code': message})
        return attrs        
