from celery import shared_task
from django.utils import timezone

from habits.models import Notification
from telegram_bot.models import TelegramBotLog
from telegram_bot.services import send_telegram_message
from users.models import User


@shared_task
def send_habit_reminder(chat_id: str, message: str) -> None:
    """
       Асинхронно отправляет напоминание о привычке в Telegram.
       :param chat_id: Telegram Chat ID пользователя.
       :param message: Текст напоминания.
    """
    send_telegram_message(chat_id, message)


@shared_task
def send_congratulation_message(chat_id: str, text: str) -> None:
    """
        Асинхронно отправляет поздравительное сообщение в Telegram.
        :param chat_id: Telegram Chat ID пользователя.
        :param text: Текст поздравления.
    """
    send_telegram_message(chat_id, text)


@shared_task
def poll_inactive_users() -> None:
    """
        Оповещает пользователей, которые за последние Х дней не были активны( у кого имеется .
        Подразумевает наличие у модели User поля `last_active`.
    """
    inactive_days = 7
    cutoff = timezone.now() - timezone.timedelta(days=inactive_days)
    # Отфильтровываем пользователей с telegram_chat_id
    inactive_users = User.objects.filter(last_active__lt=cutoff, telegram_chat_id__isnull=False)
    for user in inactive_users:
        # Проверяем, включена ли у пользователя функция notify_telegram в его профиле
        user_profile = getattr(user, 'userprofile', None)
        if user_profile and user_profile.notify_telegram:
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
    failed_logs = TelegramBotLog.objects.filter(error__isnull=False).exclude(error='')
    for log in failed_logs:
        send_telegram_message(log.telegram_chat_id, log.message)
