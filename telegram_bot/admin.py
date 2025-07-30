from .models import TelegramIntegration, TelegramBotLog
from django.contrib import admin

admin.site.register(TelegramIntegration)
admin.site.register(TelegramBotLog)
