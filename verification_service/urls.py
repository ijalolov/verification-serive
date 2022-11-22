from django.urls import path
from . import views


urlpatterns = [
    path('sendCode/sms/', view=views.SMSVerificationSendCode.as_view()),
    path('checkCode/sms/', view=views.SMSVerificationCheckCode.as_view()) 
]
