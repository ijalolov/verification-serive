from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from . import serializers
from . import models


class SMSVerificationSendCode(CreateAPIView):
    queryset = models.SMSVerification.objects.all()
    serializer_class = serializers.SMSVerificationCreateSerializer
    
    
class SMSVerificationCheckCode(GenericAPIView):
    queryset = models.SMSVerification.objects.all()
    serializer_class = serializers.SMSVerifySerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({'message': _('Confirmed.')})
