from rest_framework import serializers


class TelegramWebhookResponseSerializer(serializers.Serializer):
    status = serializers.CharField(help_text="Статус обработки")
    note = serializers.CharField(required=False, help_text="Комментарий")
    error = serializers.CharField(required=False, help_text="Ошибка")
