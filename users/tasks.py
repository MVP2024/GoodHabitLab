# from celery import shared_task
# from telegram_bot.services import send_telegram_message
# from users.models import UserProfile
# from habits.models import Habit, DailyHabitLog
# from django.utils import timezone
#
# @shared_task
# def poll_inactive_users():
#     """
#     Оповещает пользователей о невыполненных привычках согласно их настройкам напоминаний.
#     """
#     now = timezone.now()
#     today = now.date()
#     cutoff_daily = today
#     cutoff_weekly = today - timezone.timedelta(days=7)
#
#     for profile in UserProfile.objects.select_related('user').filter(
#         user__telegram_chat_id__isnull=False,
#         notify_telegram=True,
#         reminder_frequency__in=["daily", "weekly"]
#     ):
#         user = profile.user
#         freq = profile.reminder_frequency
#
#         # Проверяем reminder_time (если оно задано)
#         if profile.reminder_time:
#             # time() это просто часы:минуты
#             current = now.time().replace(second=0, microsecond=0)
#             target = profile.reminder_time.replace(second=0, microsecond=0)
#             if current != target:
#                 continue
#
#         # Собираем список привычек пользователя
#         habits = Habit.objects.filter(user=user)
#         if not habits.exists():
#             continue  # Нет привычек — не уведомлять
#
#         # Счётчик невыполненных привычек за нужный период
#         missed_count = 0
#
#         if freq == "daily":
#             # Смотрим все привычки за сегодня
#             for habit in habits:
#                 log_exists = DailyHabitLog.objects.filter(
#                     user=user, habit=habit, date=cutoff_daily, status='done'
#                 ).exists()
#                 if not log_exists:
#                     missed_count += 1
#             if missed_count > 0:
#                 msg = (
#                     f"У вас {missed_count} невыполненных привыч{'ка' if missed_count == 1 else 'ки'} за сегодня!"
#                     if missed_count > 1
#                     else "Вы сегодня пропустили привычку!"
#                 )
#                 send_telegram_message(user.telegram_chat_id, msg)
#
#         elif freq == "weekly":
#             for habit in habits:
#                 log_exists = DailyHabitLog.objects.filter(
#                     user=user,
#                     habit=habit,
#                     date__gte=cutoff_weekly,
#                     status='done'
#                 ).exists()
#                 if not log_exists:
#                     missed_count += 1
#             if missed_count > 0:
#                 msg = (
#                     f"У вас {missed_count} привыч{'ки' if missed_count > 1 else 'ка'}
#                     не выполнено за последнюю неделю!"
#                 )
#                 send_telegram_message(user.telegram_chat_id, msg)
