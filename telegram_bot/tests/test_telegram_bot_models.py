from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from telegram_bot.models import TelegramBotLog, TelegramIntegration
from users.models import User


class TelegramIntegrationModelTest(TestCase):
    """
    Тесты для модели TelegramIntegration.
    """

    def setUp(self):
        """
        Настройка тестовых данных перед каждым тестом.
        Создаем пользователя для связи с интеграцией Telegram.
        """
        self.user = User.objects.create_user(email='testuser@example.com', password='testpassword')

    def test_create_telegram_integration(self):
        """
        Проверяет успешное создание объекта TelegramIntegration.
        """
        integration = TelegramIntegration.objects.create(
            user=self.user,
            telegram_chat_id='1234567890',
            is_active=True
        )
        self.assertEqual(integration.user, self.user)
        self.assertEqual(integration.telegram_chat_id, '1234567890')
        self.assertTrue(integration.is_active)
        self.assertIsNotNone(integration.connected_at)

    def test_telegram_integration_default_is_active(self):
        """
        Проверяет, что is_active по умолчанию True.
        """
        integration = TelegramIntegration.objects.create(
            user=self.user,
            telegram_chat_id='0987654321'
        )
        self.assertTrue(integration.is_active)

    def test_telegram_integration_connected_at_auto_now_add(self):
        """
        Проверяет, что connected_at устанавливается автоматически при создании.
        """
        before_creation = timezone.now()
        integration = TelegramIntegration.objects.create(
            user=self.user,
            telegram_chat_id='1122334455'
        )
        after_creation = timezone.now()
        self.assertGreaterEqual(integration.connected_at, before_creation)
        self.assertLessEqual(integration.connected_at, after_creation)


class TelegramBotLogModelTest(TestCase):
    """
    Тесты для модели TelegramBotLog.
    """

    def setUp(self):
        """
        Настройка тестовых данных.
        Создаем пользователя и тестовые записи логов.
        """
        self.user = User.objects.create_user(email='loguser@example.com', password='logpassword')

    def test_create_telegram_bot_log_inbound(self):
        """
        Проверяет успешное создание входящего лога.
        """
        log = TelegramBotLog.objects.create(
            telegram_chat_id='chat_id_in',
            user=self.user,
            direction='in',
            message='Входящее сообщение от пользователя.'
        )
        self.assertEqual(log.telegram_chat_id, 'chat_id_in')
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.direction, 'in')
        self.assertEqual(log.message, 'Входящее сообщение от пользователя.')
        self.assertIsNotNone(log.timestamp)
        self.assertEqual(log.error, '')

    def test_create_telegram_bot_log_outbound_with_error(self):
        """
        Проверяет успешное создание исходящего лога с ошибкой.
        """
        log = TelegramBotLog.objects.create(
            telegram_chat_id='chat_id_out',
            user=self.user,
            direction='out',
            message='Исходящее сообщение с ошибкой.',
            error='Ошибка отправки: Network error.'
        )
        self.assertEqual(log.telegram_chat_id, 'chat_id_out')
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.direction, 'out')
        self.assertEqual(log.message, 'Исходящее сообщение с ошибкой.')
        self.assertIsNotNone(log.timestamp)
        self.assertEqual(log.error, 'Ошибка отправки: Network error.')

    def test_telegram_bot_log_str_representation(self):
        """
        Проверяет строковое представление объекта TelegramBotLog.
        """
        log = TelegramBotLog.objects.create(
            telegram_chat_id='12345',
            user=self.user,
            direction='out',
            message='Это очень длинное тестовое сообщение, которое должно быть обрезано в __str__ методе.'
        )
        expected_str = "Лог для чата 12345: Это очень длинное тестовое соо"
        self.assertEqual(str(log), expected_str)

    def test_telegram_bot_log_user_nullable(self):
        """
        Проверяет, что поле user может быть null.
        """
        log = TelegramBotLog.objects.create(
            telegram_chat_id='guest_chat',
            user=None,
            direction='in',
            message='Сообщение от незарегистрированного пользователя.'
        )
        self.assertIsNone(log.user)
        self.assertEqual(log.telegram_chat_id, 'guest_chat')

    def test_telegram_bot_log_error_blank(self):
        """
        Проверяет, что поле error может быть пустым.
        """
        log = TelegramBotLog.objects.create(
            telegram_chat_id='no_error_chat',
            user=self.user,
            direction='out',
            message='Сообщение без ошибок.'
        )
        self.assertEqual(log.error, '')
