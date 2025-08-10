from unittest.mock import call, patch  # Добавляем импорт 'call'

from django.test import TestCase
from django.utils import timezone

from habits.models import Notification
from telegram_bot.models import TelegramBotLog
from telegram_bot.tasks import (poll_inactive_users,
                                retry_failed_telegram_messages,
                                send_congratulation_message,
                                send_habit_reminder)
from users.models import User


class TelegramTasksTestCase(TestCase):
    """
    Набор тестов для задач Celery, связанных с Telegram ботом.
    """

    def setUp(self):
        """
        Настройка тестовых данных.
        """
        # Создаем пользователей без явного создания UserProfile,
        # так как он создается автоматически по сигналу post_save
        self.user_active = User.objects.create(
            email='active@example.com',
            telegram_chat_id='11111',
            last_active=timezone.now()
        )
        self.user_inactive = User.objects.create(
            email='inactive@example.com',
            telegram_chat_id='22222',
            last_active=timezone.now() - timezone.timedelta(days=10)  # Неактивный пользователь
        )
        self.user_inactive_no_chat_id = User.objects.create(
            email='inactive_no_chat@example.com',
            telegram_chat_id='99999',  # Изменено для уникальности
            last_active=timezone.now() - timezone.timedelta(days=10)
        )


        # Логи с ошибками для повторной отправки
        self.failed_log_1 = TelegramBotLog.objects.create(
            telegram_chat_id='33333',
            message='Тестовое сообщение 1',
            direction='out',
            error='Ошибка отправки 1'
        )
        self.failed_log_2 = TelegramBotLog.objects.create(
            telegram_chat_id='44444',
            message='Тестовое сообщение 2',
            direction='out',
            error='Ошибка отправки 2'
        )
        # Успешный лог
        self.successful_log = TelegramBotLog.objects.create(
            telegram_chat_id='55555',
            message='Успешное сообщение',
            direction='out',
            error=''
        )

    @patch('telegram_bot.tasks.send_telegram_message')
    def test_send_habit_reminder(self, mock_send_telegram_message):
        """
        Проверяет, что send_habit_reminder вызывает send_telegram_message с правильными аргументами.
        """
        chat_id = "test_chat_id"
        message = "Это напоминание о привычке!"
        send_habit_reminder(chat_id, message)
        mock_send_telegram_message.assert_called_once_with(chat_id, message)

    @patch('telegram_bot.tasks.send_telegram_message')
    def test_send_congratulation_message(self, mock_send_telegram_message):
        """
        Проверяет, что send_congratulation_message вызывает send_telegram_message с правильными аргументами.
        """
        chat_id = "test_chat_id_2"
        text = "Поздравляем с выполнением!"
        send_congratulation_message(chat_id, text)
        mock_send_telegram_message.assert_called_once_with(chat_id, text)

    @patch('habits.models.Notification.objects.create')
    def test_poll_inactive_users(self, mock_notification_create):
        """
        Проверяет, что poll_inactive_users создает уведомления для неактивных пользователей
        с привязанным Telegram chat_id.
        """
        poll_inactive_users()
        self.assertEqual(mock_notification_create.call_count, 2)
        mock_notification_create.assert_any_call(
            user=self.user_inactive,
            channel='telegram',
            notification_type='inactive_reminder',
            message="Мы заметили, что вы давно не выполняли привычки. Пора вернуться к ним!"
        )
        mock_notification_create.assert_any_call(
            user=self.user_inactive_no_chat_id,
            channel='telegram',
            notification_type='inactive_reminder',
            message="Мы заметили, что вы давно не выполняли привычки. Пора вернуться к ним!"
        )

    @patch('telegram_bot.tasks.send_telegram_message')
    def test_retry_failed_telegram_messages(self, mock_send_telegram_message):
        """
        Проверяет, что retry_failed_telegram_messages пытается повторно отправить
        только те сообщения, которые имели ошибки.
        """
        retry_failed_telegram_messages()

        self.assertEqual(mock_send_telegram_message.call_count, 2)
        mock_send_telegram_message.assert_any_call(self.failed_log_1.telegram_chat_id, self.failed_log_1.message)
        mock_send_telegram_message.assert_any_call(self.failed_log_2.telegram_chat_id, self.failed_log_2.message)
        # Убедимся, что успешный лог не был заново отправлен
        self.assertNotIn(
            (self.successful_log.telegram_chat_id, self.successful_log.message),
            [call.args for call in mock_send_telegram_message.call_args_list]
        )
