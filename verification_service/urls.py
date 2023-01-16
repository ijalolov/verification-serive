from django.urls import path
from .api_endpoints.sms import views as sms_views

app_name = "verification_service"

sms_urlpatterns = [
    path('sms/SendCode', view=sms_views.SMSSendCodeView.as_view(), name='SMSSendCode'),
    path('sms/CheckCode', view=sms_views.SMSCheckCodeView.as_view(), name='SMSCheckCode'),
]


urlpatterns = sms_urlpatterns
