from django.contrib import admin
from . import models



@admin.register(models.SMSVerification)
class SMSAdmin(admin.ModelAdmin):
    list_display = ('id', 'verification_state', 'phone_number')




@admin.register(models.EmailVerification)
class EmailAdmin(admin.ModelAdmin):
    pass
