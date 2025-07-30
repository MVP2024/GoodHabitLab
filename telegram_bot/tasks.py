from celery import shared_task
from telegram_bot.services import send_telegram_message
from users.models import User
from telegram_bot.models import TelegramBotLog
from habits.models import Notification


@shared_task
def send_habit_reminder(chat_id: str, message: str) -> None:
    """
       Асинхронно отправляет напоминание о привычке в Telegram.
       :param chat_id: Telegram Chat ID пользователя.
       :param message: Текст напоминания.
    """
    send_telegram_message(chat_id, message)


@shared_task
def send_congratulation(chat_id: str, text: str) -> None:
    """
        Асинхронно отправляет поздравительное сообщение в Telegram.
        :param chat_id: Telegram Chat ID пользователя.
        :param text: Текст поздравления.
    """
    send_telegram_message(chat_id, text)


@shared_task
def poll_inactive_users() -> None:
    """
        Оповещает пользователей, которые за последние Х дней не были активны.
        Подразумевает наличие у модели User поля `last_active`.
    """
    inactive_days = 7  # Можно настроить, сколько дней считать неактивностью
    from django.utils import timezone
    cutoff = timezone.now() - timezone.timedelta(days=inactive_days)
    inactive_users = User.objects.filter(last_active__lt=cutoff, telegram_chat_id__isnull=False)
    for user in inactive_users:
        # Создаем уведомление через систему Notification
        Notification.objects.create(
            user=user,
            channel='telegram',
            notification_type='inactive_reminder',
            message="Мы заметили, что вы давно не выполняли привычки. Пора вернуться к ним!"
        )


@shared_task
def retry_failed_telegram_messages() -> None:
    """
       Пытается повторно отправить сообщения из логов Telegram, где была ошибка отправки.
    """
    failed_logs = TelegramBotLog.objects.filter(error__isnull=False)
    for log in failed_logs:
        send_telegram_message(log.telegram_chat_id, log.message)
