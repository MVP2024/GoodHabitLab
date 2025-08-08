import logging
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.utils import timezone

from habits.models import Habit, HabitLog, Notification
from habits.tasks import (check_and_send_daily_habit_reminders,
                          send_postponed_habit_reminder)
from telegram_bot.models import TelegramBotLog
from telegram_bot.tasks import (poll_inactive_users,
                                retry_failed_telegram_messages,
                                send_congratulation_message,
                                send_habit_reminder)
from users.models import User, UserProfile


class HabitTasksTestCase(TestCase):
    """
    Набор тестов для задач Celery, связанных с привычками и Telegram ботом.
    """

    def setUp(self):
        """
        Настройка тестовых данных для всех тестов.
        """
        self.user = User.objects.create(email='test@example.com', telegram_chat_id='12345', is_active=True)
        # Убедимся, что userprofile создан, т.к. он нужен для user.userprofile.notify_telegram
        UserProfile.objects.get_or_create(user=self.user)

        self.user_no_chat_id = User.objects.create(email='no_chat_id@example.com', telegram_chat_id=None,
                                                    is_active=True)
        UserProfile.objects.get_or_create(user=self.user_no_chat_id)

        self.user_inactive_telegram = User.objects.create(email='inactive_tg@example.com', telegram_chat_id='54321',
                                                           is_active=True)
        # UserProfile создается автоматически, поэтому просто обновляем его, если он уже есть,
        # или создаем, если его почему-то нет (хотя post_save должен позаботиться об этом)
        user_profile, created = UserProfile.objects.get_or_create(user=self.user_inactive_telegram)
        user_profile.notify_telegram = False
        user_profile.save()

        self.habit_daily = Habit.objects.create(
            user=self.user,
            title='Ежедневная привычка',
            description='Тестовое описание',
            periodicity='daily',
            selected_weekdays=['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс'],
            place='Дом',
            duration=60,
            is_active=True,
            planned_time=timezone.now().time().replace(second=0, microsecond=0)
        )
        # Получаем текущий день недели на русском для создания тестовой привычки
        current_day_en = timezone.now().strftime('%a').lower()
        weekday_map = {
            'mon': 'пн', 'tue': 'вт', 'wed': 'ср', 'thu': 'чт',
            'fri': 'пт', 'sat': 'сб', 'sun': 'вс'
        }
        current_weekday_ru = weekday_map.get(current_day_en, 'пн')  # Устанавливаем 'пн' по умолчанию

        self.habit_custom_today = Habit.objects.create(
            user=self.user,
            title='Привычка на сегодня',
            description='Тестовое описание',
            periodicity='custom',
            selected_weekdays=[current_weekday_ru],
            place='Офис',
            duration=30,
            is_active=True,
            planned_time=timezone.now().time().replace(second=0, microsecond=0)
        )
        # Для habit_custom_tomorrow: если сегодня вторник, то 'ср' будет завтра.
        # Если сегодня среда, то 'чт' будет завтра и т.д.
        # Используем маппинг для определения "завтрашнего" дня.
        # Проверяем, что current_day_en есть в ключах, чтобы избежать ошибок индексации
        if current_day_en in weekday_map:
            current_day_index = list(weekday_map.keys()).index(current_day_en)
            tomorrow_weekday_index = (current_day_index + 1) % 7
            tomorrow_weekday_en = list(weekday_map.keys())[tomorrow_weekday_index]
            tomorrow_weekday_ru = weekday_map.get(tomorrow_weekday_en, 'вт')  # Устанавливаем 'вт' по умолчанию
        else:
            tomorrow_weekday_ru = 'вт'  # Если текущий день не найден, по умолчанию вторник

        self.habit_custom_tomorrow = Habit.objects.create(
            user=self.user,
            title='Привычка на завтра',
            description='Тестовое описание',
            periodicity='custom',
            selected_weekdays=[tomorrow_weekday_ru],
            place='Спортзал',
            duration=45,
            is_active=True,
            planned_time=timezone.now().time().replace(second=0, microsecond=0)
        )
        self.habit_no_weekdays = Habit.objects.create(
            user=self.user,
            title='Привычка без дней недели',
            description='Тестовое описание',
            periodicity='custom',
            selected_weekdays=[],
            place='Где угодно',
            duration=10,
            is_active=True,
            planned_time=timezone.now().time().replace(second=0, microsecond=0)
        )
        self.habit_no_chat_id = Habit.objects.create(
            user=self.user_no_chat_id,
            title='Привычка без chat_id',
            description='Тестовое описание',
            periodicity='daily',
            selected_weekdays=['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс'],
            place='Дом',
            duration=60,
            is_active=True,
            planned_time=timezone.now().time().replace(second=0, microsecond=0)
        )
        self.habit_inactive_telegram = Habit.objects.create(
            user=self.user_inactive_telegram,
            title='Привычка с отключенными уведомлениями',
            description='Тестовое описание',
            periodicity='daily',
            selected_weekdays=['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс'],
            place='Дом',
            duration=60,
            is_active=True,
            planned_time=timezone.now().time().replace(second=0, microsecond=0)
        )

        # Тестовые данные для TelegramTaskTestCase
        self.user_active_tg_test = User.objects.create(
            email='active_tg_test@example.com',
            telegram_chat_id='11111',
            last_active=timezone.now()
        )
        UserProfile.objects.get_or_create(user=self.user_active_tg_test)

        self.user_inactive_tg_test = User.objects.create(
            email='inactive_tg_test@example.com',
            telegram_chat_id='22222',
            last_active=timezone.now() - timezone.timedelta(days=10)  # Неактивный пользователь
        )
        UserProfile.objects.get_or_create(user=self.user_inactive_tg_test)

        self.user_inactive_no_chat_id_tg_test = User.objects.create(
            email='inactive_no_chat_tg_test@example.com',
            telegram_chat_id='99999',  # Изменено для уникальности
            last_active=timezone.now() - timezone.timedelta(days=10)
        )
        UserProfile.objects.get_or_create(user=self.user_inactive_no_chat_id_tg_test)

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

    @patch('telegram_bot.tasks.send_habit_reminder.delay')
    def test_check_and_send_daily_habit_reminders_sends_reminders(self, mock_send_habit_reminder_delay):
        """
        Проверяет, что check_and_send_daily_habit_reminders отправляет напоминания
        для активных привычек с правильной периодичностью.
        """
        check_and_send_daily_habit_reminders()

        # Ожидаем 2 вызова: для habit_daily и habit_custom_today
        self.assertEqual(mock_send_habit_reminder_delay.call_count, 2)
        mock_send_habit_reminder_delay.assert_any_call(
            str(self.user.telegram_chat_id),
            f"Напоминание: {self.habit_daily.title} — {self.habit_daily.description}"
        )
        mock_send_habit_reminder_delay.assert_any_call(
            str(self.user.telegram_chat_id),
            f"Напоминание: {self.habit_custom_today.title} — {self.habit_custom_today.description}"
        )

        self.assertTrue(HabitLog.objects.filter(habit=self.habit_daily, user=self.user, date=timezone.now().date()).exists())
        self.assertTrue(HabitLog.objects.filter(habit=self.habit_custom_today, user=self.user, date=timezone.now().date()).exists())
        self.assertFalse(HabitLog.objects.filter(habit=self.habit_custom_tomorrow, user=self.user, date=timezone.now().date()).exists())


    @patch('telegram_bot.tasks.send_habit_reminder.delay')
    def test_check_and_send_daily_habit_reminders_no_chat_id(self, mock_send_habit_reminder_delay):
        """
        Проверяет, что check_and_send_daily_habit_reminders не отправляет напоминания
        пользователям без telegram_chat_id.
        """
        # Сначала убедимся, что habit_no_chat_id соответствует текущему дню для его включения в выборку
        # Это важно, так как get_or_create в check_and_send_daily_habit_reminders
        # будет вызван даже для пользователей без chat_id, если они попадают в фильтр по времени.
        # Однако само send_habit_reminder.delay вызвано не будет.
        self.habit_no_chat_id.planned_time = timezone.now().time().replace(second=0, microsecond=0)
        self.habit_no_chat_id.save()

        check_and_send_daily_habit_reminders()

        # Проверяем, что напоминания не были отправлены для пользователя без chat_id
        # (user_no_chat_id, telegram_chat_id=None)
        # Важно: здесь мы ищем по chat_id, который может быть None,
        # поэтому убеждаемся, что mock.call_args_list не содержит вызовов с None
        self.assertFalse(
            any(call_arg[0][0] is None for call_arg in mock_send_habit_reminder_delay.call_args_list)
        )
        # Проверяем, что логи для этого пользователя не создались, т.к. send_habit_reminder.delay не вызывается
        self.assertFalse(HabitLog.objects.filter(habit=self.habit_no_chat_id).exists())


    @patch('telegram_bot.tasks.send_habit_reminder.delay')
    def test_check_and_send_daily_habit_reminders_inactive_telegram(self, mock_send_habit_reminder_delay):
        """
        Проверяет, что check_and_send_daily_habit_reminders не отправляет напоминания
        пользователям, у которых notify_telegram установлен в False.
        """
        check_and_send_daily_habit_reminders()
        # Проверяем, что для пользователя с отключенными уведомлениями Telegram
        # не было вызовов send_habit_reminder.delay
        self.assertFalse(
            any(str(self.user_inactive_telegram.telegram_chat_id) in str(call) for call in mock_send_habit_reminder_delay.call_args_list))
        # Проверяем, что логи для этой привычки не создались, т.к. отправка пропущена
        self.assertFalse(HabitLog.objects.filter(habit=self.habit_inactive_telegram).exists())


    @patch('habits.tasks.logger.warning')  # Мокируем логгер
    @patch('telegram_bot.tasks.send_habit_reminder.delay')
    def test_check_and_send_daily_habit_reminders_no_weekdays(self, mock_send_habit_reminder_delay, mock_logger_warning):
        """
        Проверяет, что check_and_send_daily_habit_reminders логирует предупреждение
        и пропускает привычки без выбранных дней недели.
        """
        check_and_send_daily_habit_reminders()
        mock_logger_warning.assert_called_with(
            f"Привычка '{self.habit_no_weekdays.title}' пользователя {self.habit_no_weekdays.user.email} не имеет выбранных дней недели. Пропускаем.")
        self.assertFalse(HabitLog.objects.filter(habit=self.habit_no_weekdays).exists())
        self.assertFalse(
            any(f"Напоминание: {self.habit_no_weekdays.title}" in str(call) for call in
                mock_send_habit_reminder_delay.call_args_list))


    @patch('telegram_bot.tasks.send_habit_reminder.delay')  # Изменено на telegram_bot.tasks.send_habit_reminder.delay
    def test_send_postponed_habit_reminder_not_done(self, mock_send_habit_reminder_delay):
        """
        Проверяет, что send_postponed_habit_reminder отправляет сообщение,
        если привычка не выполнена.
        """
        habit_log = HabitLog.objects.create(
            habit=self.habit_daily,
            user=self.user,
            date=timezone.now().date(),
            is_done=False
        )
        chat_id = str(self.user.telegram_chat_id)
        send_postponed_habit_reminder(chat_id, habit_log.id)

        # Проверяем, что send_habit_reminder.delay был вызван с правильными аргументами
        mock_send_habit_reminder_delay.assert_called_once_with(
            chat_id,
            f"Повторное напоминание: {self.habit_daily.title} — {self.habit_daily.description}"
        )

    @patch('telegram_bot.tasks.send_habit_reminder.delay')  # Изменено на telegram_bot.tasks.send_habit_reminder.delay
    def test_send_postponed_habit_reminder_done(self, mock_send_habit_reminder_delay):
        """
        Проверяет, что send_postponed_habit_reminder не отправляет сообщение,
        если привычка уже выполнена.
        """
        habit_log = HabitLog.objects.create(
            habit=self.habit_daily,
            user=self.user,
            date=timezone.now().date(),
            is_done=True
        )
        chat_id = self.user.telegram_chat_id
        send_postponed_habit_reminder(str(chat_id), habit_log.id)
        mock_send_habit_reminder_delay.assert_not_called()

    @patch('telegram_bot.tasks.send_habit_reminder.delay')  # Изменено на telegram_bot.tasks.send_habit_reminder.delay
    def test_send_postponed_habit_reminder_log_does_not_exist(self, mock_send_habit_reminder_delay):
        """
        Проверяет, что send_postponed_habit_reminder корректно обрабатывает
        несуществующий HabitLog.
        """
        chat_id = self.user.telegram_chat_id
        send_postponed_habit_reminder(str(chat_id), 99999)
        mock_send_habit_reminder_delay.assert_not_called()

    @patch('telegram_bot.tasks.send_habit_reminder.delay')
    def test_check_and_send_daily_habit_reminders_log_already_exists(self, mock_send_habit_reminder_delay):
        """
        Проверяет, что check_and_send_daily_habit_reminders использует get_or_create
        и не создает дубликаты логов.
        """
        # Создаем лог заранее для habit_daily
        HabitLog.objects.create(
            habit=self.habit_daily,
            user=self.user,
            date=timezone.now().date(),
            is_done=False
        )
        # Ожидаем, что 2 привычки (daily и custom_today) будут обработаны.
        # Для habit_daily будет get_or_create, для habit_custom_today будет create.
        initial_log_count = HabitLog.objects.count()

        check_and_send_daily_habit_reminders()

        # Теперь должно быть 2 лога: один существующий (habit_daily),
        # и один новый (habit_custom_today), так как он соответствует текущему дню.
        self.assertEqual(HabitLog.objects.count(), initial_log_count + 1)
        self.assertTrue(HabitLog.objects.filter(habit=self.habit_daily, user=self.user, date=timezone.now().date()).exists())
        self.assertTrue(HabitLog.objects.filter(habit=self.habit_custom_today, user=self.user, date=timezone.now().date()).exists())
        self.assertEqual(mock_send_habit_reminder_delay.call_count, 2) # Вызовы для habit_daily и habit_custom_today


    @patch('habits.models.Notification.objects.create')
    def test_poll_inactive_users(self, mock_notification_create):
        """
        Проверяет, что poll_inactive_users создает уведомления для неактивных пользователей
        с привязанным Telegram chat_id.
        """
        poll_inactive_users()
        self.assertEqual(mock_notification_create.call_count, 2)
        mock_notification_create.assert_any_call(
            user=self.user_inactive_tg_test,
            channel='telegram',
            notification_type='inactive_reminder',
            message="Мы заметили, что вы давно не выполняли привычки. Пора вернуться к ним!"
        )
        mock_notification_create.assert_any_call(
            user=self.user_inactive_no_chat_id_tg_test,
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
