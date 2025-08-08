from rest_framework import serializers


class TelegramWebhookResponseSerializer(serializers.Serializer):
    status = serializers.CharField(
        help_text="Статус обработки",
        error_messages={'required': 'Это поле обязательно.'}
    )
    note = serializers.CharField(required=False, help_text="Комментарий", allow_blank=True)
    error = serializers.CharField(required=False, help_text="Ошибка", allow_blank=True)


# class MessageSerializer(serializers.Serializer):
#     message_id = serializers.IntegerField()
#     from_user = serializers.JSONField(help_text="Информация о пользователе, отправившем сообщение")  # Full User object
#     chat = serializers.JSONField(help_text="Информация о чате")  # Full Chat object
#     date = serializers.IntegerField(help_text="Дата отправки сообщения (Unix timestamp)")
#     text = serializers.CharField(required=False, allow_blank=True, help_text="Текст сообщения")
#
#
# class CallbackQuerySerializer(serializers.Serializer):
#     id = serializers.CharField()
#     from_user = serializers.JSONField(help_text="Информация о пользователе, нажавшем кнопку")  # Full User object
#     message = MessageSerializer(required=False, help_text="Сообщение, к которому относится callback_query")
#     inline_message_id = serializers.CharField(required=False, allow_blank=True)
#     chat_instance = serializers.CharField()
#     data = serializers.CharField(help_text="Данные, прикрепленные к кнопке")
#
#
# class TelegramUpdateSerializer(serializers.Serializer):
#     update_id = serializers.IntegerField(help_text="Уникальный идентификатор обновления")
#     message = MessageSerializer(required=False, help_text="Новое входящее сообщение")
#     callback_query = CallbackQuerySerializer(required=False, help_text="Входящий запрос обратного вызова от кнопки")

    # edited_message = MessageSerializer(required=False)
    # channel_post = MessageSerializer(required=False)
    # edited_channel_post = MessageSerializer(required=False)
    # inline_query = InlineQuerySerializer(required=False) # нужно мне будет создать InlineQuerySerializer
    # chosen_inline_result = ChosenInlineResultSerializer(required=False) # нужно мне будет создать ChosenInlineResultSerializer
    # shipping_query = ShippingQuerySerializer(required=False)
    # pre_checkout_query = PreCheckoutQuerySerializer(required=False)
    # poll = PollSerializer(required=False)
    # poll_answer = PollAnswerSerializer(required=False)
    # my_chat_member = ChatMemberUpdatedSerializer(required=False)
    # chat_member = ChatMemberUpdatedSerializer(required=False)
    # chat_join_request = ChatJoinRequestSerializer(required=False)

    # def validate(self, data):
    #     # Проверяем, что есть хотя бы один из ожидаемых типов обновлений
    #     if not any(key in data for key in ['message', 'callback_query']):
    #         raise serializers.ValidationError("Объект обновления Telegram должен содержать 'message' или 'callback_query'.")
    #     return data
