from django.test import TestCase

from telegram_bot.serializers import TelegramWebhookResponseSerializer


class TelegramWebhookResponseSerializerTest(TestCase):
    """
    Тесты для сериализатора TelegramWebhookResponseSerializer.
    Этот сериализатор используется для формирования ответа на входящий вебхук Telegram.
    Обеспечивают 100% покрытие строк.
    """

    def test_valid_data(self):
        """
        Проверяет сериализатор с полным набором валидных данных.
        """
        data = {
            'status': 'success',
            'note': 'Операция выполнена успешно.',
            'error': ''
        }
        serializer = TelegramWebhookResponseSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['status'], 'success')
        self.assertEqual(serializer.validated_data['note'], 'Операция выполнена успешно.')
        self.assertEqual(serializer.validated_data['error'], '')

    def test_valid_data_without_optional_fields(self):
        """
        Проверяет сериализатор с валидными данными, но без необязательных полей 'note' и 'error'.
        """
        data = {
            'status': 'failure'
        }
        serializer = TelegramWebhookResponseSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['status'], 'failure')
        self.assertNotIn('note', serializer.validated_data)
        self.assertNotIn('error', serializer.validated_data)

    def test_missing_status_field(self):
        """
        Проверяет ошибку валидации при отсутствии обязательного поля 'status'.
        """
        data = {
            'note': 'Что-то пошло не так.',
            'error': 'Неизвестная ошибка.'
        }
        serializer = TelegramWebhookResponseSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('status', serializer.errors)

        self.assertEqual(str(serializer.errors['status'][0]), 'Это поле обязательно.')

    def test_empty_status_field(self):
        """
        Проверяет ошибку валидации при пустом обязательном поле 'status'.
        """
        data = {
            'status': '',
            'note': 'Примечание',
            'error': 'Ошибка'
        }
        serializer = TelegramWebhookResponseSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('status', serializer.errors)
        self.assertEqual(str(serializer.errors['status'][0]), 'Это поле не может быть пустым.')

    def test_extra_fields_are_ignored(self):
        """
        Проверяет, что лишние поля в данных игнорируются сериализатором.
        """
        data = {
            'status': 'processed',
            'note': 'Обработано',
            'extra_field': 'лишняя информация'
        }
        serializer = TelegramWebhookResponseSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertIn('status', serializer.validated_data)
        self.assertIn('note', serializer.validated_data)
        self.assertNotIn('extra_field', serializer.validated_data)

    def test_error_field_can_be_empty_string(self):
        """
        Проверяет, что поле 'error' может быть пустой строкой.
        """
        data = {
            'status': 'completed',
            'error': ''
        }
        serializer = TelegramWebhookResponseSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertIn('status', serializer.validated_data)
        self.assertEqual(serializer.validated_data['error'], '')