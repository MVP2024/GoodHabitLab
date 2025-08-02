import logging

from celery import shared_task
from django.utils import timezone

from habits.models import Habit, HabitLog
from telegram_bot.services import send_telegram_message
from users.models import User
from datetime import date, datetime, timedelta

logger = logging.getLogger(__name__)


@shared_task
def send_habit_reminder(chat_id: str, message: str, habit_log_id: int) -> None:
    """
    Асинхронно отправляет напоминание одному пользователю в Telegram.
    """
    send_telegram_message(chat_id, message)


@shared_task
def send_congratulation(chat_id: str, text: str) -> None:
    """
    Асинхронно отправляет поздравительное сообщение в Telegram.
    """
    send_telegram_message(chat_id, text)


@shared_task
def check_and_send_daily_habit_reminders():
    """
    Ежедневно рассылает напоминание всем пользователям по их активным привычкам,
    если пришло их плановое время и не было выполнено (или любое другое правило).
    """
    now = timezone.now()
    current_time = now.time()
    today_weekday = now.strftime('%a').lower()  # 'mon', 'tue', etc.

    # Маппинг для дней недели на русском
    weekday_map = {
        'mon': 'пн', 'tue': 'вт', 'wed': 'ср', 'thu': 'чт',
        'fri': 'пт', 'sat': 'сб', 'sun': 'вс'
    }
    current_weekday_ru = weekday_map[today_weekday]

    # Округляем до ближайшей минуты для сравнения
    current_time_rounded = current_time.replace(second=0, microsecond=0)
    logger.info(f"Запущена задача {check_and_send_daily_habit_reminders}. Текущее время: {current_time_rounded}, "
                f"День недели: {current_weekday_ru}")


    # Получаем привычки, для которых запланировано напоминание в текущую минуту
    habits_to_remind = Habit.objects.filter(
        is_active=True,
        planned_time__hour=current_time_rounded.hour,
        planned_time__minute=current_time_rounded.minute,
        user__telegram_chat_id__isnull=False  # Убедимся, что у пользователя есть chat_id
    ).select_related('user')  # Оптимизация запроса

    logger.info(f"Найдено {habits_to_remind.count()} привычек для напоминания в {current_time_rounded}.")


    for habit in habits_to_remind:
        # Улучшенная логика для определения, нужно ли отправлять напоминание
        should_send = (
            habit.periodicity == 'daily' or
            (habit.periodicity == 'weekly' and now.weekday() == 0) or  # Понедельник
            (habit.periodicity == 'monthly' and now.day == 1) or  # Первое число месяца
            (habit.periodicity == 'custom' and current_weekday_ru in habit.selected_weekdays)
        )

        if should_send:
            user = habit.user
            if user and user.telegram_chat_id:
                message = f"Напоминание: {habit.title} — {habit.description}"
                logger.info(
                    f"Отправка напоминания для привычки '{habit.title}' пользователю {user.email} на chat_id {user.telegram_chat_id}")
                # Создаем лог привычки для текущего дня, если его нет
                habit_log, _ = HabitLog.objects.get_or_create(
                    habit=habit,
                    user=user,
                    date=now.date(),
                    defaults={'is_done': False}  # По умолчанию не выполнено
                )
                habit_log.last_reminded_at = now  # Обновляем время последнего напоминания
                habit_log.save()
                send_habit_reminder.delay(str(user.telegram_chat_id), message, habit_log.id)
            else:
                logger.warning(
                    f"Не удалось отправить напоминание для привычки '{habit.title}'. "
                    f"Пользователь или {user.telegram_chat_id} отсутствуют.")
        else:
            logger.info(
                f"Привычка '{habit.title}' не соответствует условиям отправки "
                f"напоминания сегодня ({habit.periodicity}, {habit.selected_weekdays}).")


@shared_task
def send_postponed_habit_reminder(chat_id: str, habit_log_id: int):
    """
    Отправляет повторное напоминание через 2 часа, если привычка не отмечена выполненной на сегодня.
    """
    try:
        habit_log = HabitLog.objects.get(id=habit_log_id, user__telegram_chat_id=chat_id)
        habit = habit_log.habit
    except HabitLog.DoesNotExist:
        logger.warning(f"Попытка отложенного напоминания для несуществующего HabitLog ID: {habit_log_id} или некорректного chat_id: {chat_id}")
        return

    # Проверяем: не выполнена ли привычка за сегодня?
    # Если habit_log.is_done уже True, значит привычка выполнена.
    if habit_log.is_done:
        logger.info(f"Привычка '{habit.title}' (лог ID: {habit_log_id}) уже выполнена, отложенное напоминание отменено.")
        return

    text = f"Повторное напоминание: {habit.title} — {habit.description}"
    send_telegram_message(chat_id, text)
