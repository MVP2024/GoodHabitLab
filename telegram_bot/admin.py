from django.contrib import admin

from .models import TelegramBotLog, TelegramIntegration

admin.site.register(TelegramIntegration)
admin.site.register(TelegramBotLog)
