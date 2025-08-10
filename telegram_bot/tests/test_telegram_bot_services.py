import os
from unittest.mock import MagicMock, patch

import requests
from django.conf import settings
from django.test import TestCase, override_settings

from telegram_bot.services import send_telegram_message


@override_settings(TELEGRAM_BOT_TOKEN="test_token",
                   TELEGRAM_API_URL="https://api.telegram.org/bottest_token/")
class SendTelegramMessageTest(TestCase):
    """
    Тесты для функции `send_telegram_message` в `telegram_bot/services.py`.
    Обеспечивает 100% покрытие функции `send_telegram_message`.
    """

    def setUp(self):
        """
        Настройка тестовых данных и переменных окружения перед каждым тестом.
        Устанавливаем заглушки для токена и URL Telegram API.
        """
        self.chat_id = "123456789"
        self.message = "Hello, Telegram!"
        self.expected_url = f"{settings.TELEGRAM_API_URL}sendMessage"
        self.expected_payload = {
            "chat_id": self.chat_id,
            "text": self.message,
            "parse_mode": "HTML",
        }

    @patch('requests.post')
    def test_send_telegram_message_success(self, mock_post):
        """
        Проверяет успешную отправку сообщения в Telegram.
        Мокируем `requests.post` для имитации успешного ответа от API Telegram.
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True, "result": {"message_id": 123}}
        mock_response.raise_for_status.return_value = None  # Убедимся, что не будет вызвано исключение
        mock_post.return_value = mock_response

        result = send_telegram_message(self.chat_id, self.message)

        mock_post.assert_called_once_with(self.expected_url, data=self.expected_payload)
        self.assertEqual(result, {"ok": True, "result": {"message_id": 123}})

    @patch('requests.post')
    def test_send_telegram_message_http_error(self, mock_post):
        """
        Проверяет обработку HTTP ошибок при отправке сообщения.
        Мокируем `requests.post` для имитации HTTP ошибки (например, 404 или 500).
        """
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Bad Request")
        mock_post.return_value = mock_response

        result = send_telegram_message(self.chat_id, self.message)

        mock_post.assert_called_once_with(self.expected_url, data=self.expected_payload)
        self.assertIsNone(result)

    @patch('requests.post')
    def test_send_telegram_message_connection_error(self, mock_post):
        """
        Проверяет обработку ошибок соединения (например, отсутствие интернета).
        Мокируем `requests.post` для имитации `ConnectionError`.
        """
        mock_post.side_effect = requests.exceptions.ConnectionError("Network unreachable")

        result = send_telegram_message(self.chat_id, self.message)

        mock_post.assert_called_once_with(self.expected_url, data=self.expected_payload)
        self.assertIsNone(result)

    @patch('requests.post')
    def test_send_telegram_message_timeout(self, mock_post):
        """
        Проверяет обработку таймаутов при отправке сообщения.
        Мокируем `requests.post` для имитации `Timeout`.
        """
        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")

        result = send_telegram_message(self.chat_id, self.message)

        mock_post.assert_called_once_with(self.expected_url, data=self.expected_payload)
        self.assertIsNone(result)
