from django.urls import path
from . import views


urlpatterns = [
    path('sendCode/', view=views.SMSVerificationSendCode.as_view()),  
    path('checkCode/', view=views.SMSVerificationCheckCode.as_view())  
]