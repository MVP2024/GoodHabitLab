import logging

from celery import shared_task
from django.utils import timezone

from habits.models import Habit, HabitLog
from telegram_bot.tasks import send_habit_reminder

logger = logging.getLogger(__name__)


@shared_task
def check_and_send_daily_habit_reminders():
    """
    Рассылает напоминания пользователям по активным привычкам,
    если пришло их плановое время. Учитывает настройки периодичности.
    """
    now = timezone.now()
    current_time = now.time().replace(second=0, microsecond=0)
    today_weekday = now.strftime('%a').lower()

    weekday_map = {
        'mon': 'пн', 'tue': 'вт', 'wed': 'ср', 'thu': 'чт',
        'fri': 'пт', 'sat': 'сб', 'sun': 'вс'
    }
    current_weekday_ru = weekday_map.get(today_weekday, '')

    logger.info(
        f"Запущена задача {check_and_send_daily_habit_reminders.__name__}. Текущее время: {current_time}, День недели: {current_weekday_ru}")

    habits_to_remind = Habit.objects.filter(
        is_active=True,
        planned_time__hour=current_time.hour,
        planned_time__minute=current_time.minute,
        user__telegram_chat_id__isnull=False
    ).select_related('user', 'user__userprofile')

    logger.info(f"Найдено {habits_to_remind.count()} активных привычек для напоминания в {current_time}.")

    # Инициализируем счётчик здесь, для отслеживания пропущенных привычек
    skipped_habits_count = 0

    for habit in habits_to_remind:
        user = habit.user
        user_profile = getattr(user, 'userprofile', None)

        if user_profile and not user_profile.notify_telegram:
            logger.info(
                f"Напоминания в Telegram для пользователя {user.email} отключены в профиле. "
                f"Пропускаем привычку '{habit.title}'.")
            skipped_habits_count += 1
            continue

        if not habit.selected_weekdays:
            logger.warning(
                f"Привычка '{habit.title}' пользователя {user.email} не имеет выбранных дней недели. Пропускаем.")
            skipped_habits_count += 1
            continue

        if current_weekday_ru in habit.selected_weekdays:
            message = f"Напоминание: {habit.title} — {habit.description}"
            logger.info(
                f"Отправка напоминания для привычки '{habit.title}' пользователю {user.email} "
                f"на chat_id {user.telegram_chat_id}")

            habit_log, _ = HabitLog.objects.get_or_create(
                habit=habit,
                user=user,
                date=now.date(),
                defaults={'is_done': False}
            )
            habit_log.last_reminded_at = now
            habit_log.save()

            send_habit_reminder.delay(str(user.telegram_chat_id), message)
        else:
            logger.info(
                f"Привычка '{habit.title}' пользователя {user.email} не соответствует условиям отправки напоминания сегодня ({habit.selected_weekdays}).")

    logger.info(f"Обработано привычек: {habits_to_remind.count()}, "
                f"отправлено: {habits_to_remind.count() - skipped_habits_count}, "
                f"пропущено: {skipped_habits_count}")


@shared_task
def send_postponed_habit_reminder(chat_id: str, habit_log_id: int):
    """
    Отправляет повторное напоминание, если привычка не отмечена выполненной на сегодня.

    :param chat_id: Telegram Chat ID пользователя.
    :param habit_log_id: ID лога привычки, для которого отправляется повторное напоминание.
    """
    try:
        # Убедимся, что лог принадлежит пользователю с данным chat_id
        habit_log = HabitLog.objects.select_related('habit').get(
            id=habit_log_id,
            user__telegram_chat_id=chat_id
        )
        habit = habit_log.habit
    except HabitLog.DoesNotExist:
        logger.warning(
            f"Попытка отложенного напоминания для несуществующего HabitLog ID: {habit_log_id} или некорректного chat_id: {chat_id}")
        return

    if habit_log.is_done:
        logger.info(
            f"Привычка '{habit.title}' (лог ID: {habit_log_id}) уже выполнена, отложенное напоминание отменено.")
        return

    text = f"Повторное напоминание: {habit.title} — {habit.description}"
    send_habit_reminder.delay(chat_id, text)
