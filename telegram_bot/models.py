from django.db import models

from users.models import User


class TelegramIntegration(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    telegram_chat_id = models.CharField(max_length=64)
    is_active = models.BooleanField(default=True)
    connected_at = models.DateTimeField(auto_now_add=True)


class TelegramBotLog(models.Model):
    telegram_chat_id = models.CharField(max_length=64)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    direction = models.CharField(max_length=10, choices=[('in', 'Входящее'), ('out', 'Исходящее')])
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    error = models.TextField(blank=True)

    def __str__(self):
        return f"Лог для чата {self.telegram_chat_id}: {self.message[:30]}"
