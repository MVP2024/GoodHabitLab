from habits.models import Habit, HabitLog
from users.models import User, UserProfile
from telegram_bot.services import send_telegram_message, \
    send_telegram_message_with_keyboard, remove_inline_keyboard
from habits.tasks import send_postponed_habit_reminder
from datetime import date, datetime, timedelta
import json
from typing import Any, Dict, Optional
from django.http import HttpRequest
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import TelegramWebhookResponseSerializer
from drf_spectacular.utils import extend_schema, OpenApiExample
import logging

logger = logging.getLogger(__name__)


class TelegramWebhookView(APIView):
    authentication_classes: list[Any] = []
    permission_classes: list[Any] = []

    @extend_schema(
        summary="Webhook для Telegram-бота",
        description="Этот эндпоинт принимает POST-запросы от Telegram Bot API.\n"
                    "Возвращает статус обработки. Если ошибка — возвращает описание ошибки.",
        request=None,
        responses={
            200: TelegramWebhookResponseSerializer,
            400: TelegramWebhookResponseSerializer,
        },
        examples=[
            OpenApiExample(
                "Успешная обработка",
                value={"status": "ok", "note": "user already registered"},
                response_only=True,
            ),
            OpenApiExample(
                "Ошибка JSON",
                value={"error": "Invalid JSON"},
                response_only=True,
            ),
        ],
    )
    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Response:
        try:
            update: Dict[str, Any] = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            logger.error("Неверный JSON, полученный от веб-хука Telegram.")
            return Response({"error": "Неверный JSON"}, status=status.HTTP_400_BAD_REQUEST)

        # --- CALLBACK QUERY (КНОПКИ) ---
        if "callback_query" in update:
            callback = update["callback_query"]
            data = callback["data"]
            chat_id = str(callback["message"]["chat"]["id"])
            message_id = int(callback["message"]["message_id"])  # Получаем message_id

            try:
                if data.startswith("done_"):
                    habit_log_id = int(data.split("_")[1])
                    try:
                        user = User.objects.get(telegram_chat_id=chat_id)
                        habit_log = HabitLog.objects.get(id=habit_log_id, user=user)
                    except (
                            User.DoesNotExist, HabitLog.DoesNotExist):
                        send_telegram_message(chat_id, "Ошибка: запись о привычке не найдена "
                                                       "или не принадлежит вам.")
                        return Response({"error": "habit log не найден"})

                    if not habit_log.is_done:  # Проверка, чтобы не отмечать выполненной дважды
                        habit_log.is_done = True
                        habit_log.save()
                        send_telegram_message(chat_id,
                                              f"Поздравляем! Привычка '{habit_log.habit.title}' "
                                              f"отмечена как выполненная.")
                        remove_inline_keyboard(chat_id, message_id)  # Удаляем кнопки
                    else:
                        send_telegram_message(chat_id,
                                              f"Привычка '{habit_log.habit.title}' уже была "
                                              f"отмечена как выполненная.")
                    return Response({"status": "ok"})

                elif data.startswith("postpone_2h_"):
                    habit_log_id = int(data.split("_")[2])
                    eta = datetime.now() + timedelta(hours=2)
                    send_postponed_habit_reminder.apply_async(args=[chat_id, habit_log_id], eta=eta)
                    send_telegram_message(chat_id, "Привычка отложена. Напоминание придёт через 2 часа.")
                    remove_inline_keyboard(chat_id, message_id)  # Удаляем кнопки
                    return Response({"status": "ok"})

                elif data.startswith("habit_stop:"):
                    try:
                        user = User.objects.get(telegram_chat_id=chat_id)
                        profile, _ = UserProfile.objects.get_or_create(user=user)
                        profile.notify_telegram = False
                        profile.save()
                        send_telegram_message(chat_id,
                                              "Напоминания отключены. "
                                              "Чтобы снова получать — используйте /start.")
                        remove_inline_keyboard(chat_id, message_id)  # Удаляем кнопки
                    except User.DoesNotExist:
                        send_telegram_message(chat_id, "Вы не были зарегистрированы в системе.")
                    except Exception as e:
                        logger.error(f"Ошибка при отключении напоминаний: {e}")
                        send_telegram_message(chat_id, "Ошибка при отключении напоминаний.")
                    return Response({"status": "ok"})

                elif data == "show_habits":
                    try:
                        user = User.objects.get(telegram_chat_id=chat_id)
                        habits = Habit.objects.filter(user=user, is_active=True)
                        if not habits:
                            send_telegram_message(chat_id, "У вас нет активных привычек.")
                        else:
                            msg = "Ваши активные привычки:\n\n" + "\n".join([f"• {h.title}" for h in habits])
                            send_telegram_message(chat_id, msg)
                        remove_inline_keyboard(chat_id, message_id)  # Удаляем кнопки
                    except User.DoesNotExist:
                        send_telegram_message(chat_id,
                                              "Аккаунт не найден. Пожалуйста, введите /start для регистрации.")
                    return Response({"status": "ok"})

                elif data == "help":
                    send_telegram_message(
                        chat_id,
                        "Доступные команды:\n/start — основное меню\n/stop — отключить напоминания\n"
                        "Используйте кнопки для взаимодействия с привычками."
                    )
                    remove_inline_keyboard(chat_id, message_id)  # Удаляем кнопки
                    return Response({"status": "ok"})

                else:
                    logger.warning(f"Неизвестный callback_data: {data}")
                    send_telegram_message(chat_id, "Неизвестная команда.")
                    return Response({"status": "ok", "note": "unknown callback_data"})

            except Exception as e:
                logger.error(f"Ошибка при обработке callback_query: {e}", exc_info=True)
                send_telegram_message(chat_id, "Произошла внутренняя ошибка при обработке запроса. "
                                               "Попробуйте еще раз.")
                return Response({"error": "internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # --- СООБЩЕНИЕ ---
        message: Optional[Dict[str, Any]] = update.get("message")
        if not message:
            return Response({"status": "ok"}, status=status.HTTP_200_OK)

        chat_id: str = str(message["chat"]["id"])
        text: str = message.get("text", "").strip()

        if text == "/start":
            try:
                user = User.objects.get(telegram_chat_id=chat_id)
                buttons = [
                    [{"text": "Мои привычки", "callback_data": "show_habits"}],
                    [{"text": "Помощь", "callback_data": "help"}],
                    [{"text": "Отключить напоминания", "callback_data": f"habit_stop:0"}],
                ]
                send_telegram_message_with_keyboard(
                    chat_id,
                    "Добро пожаловать обратно! Выберите действие:",
                    buttons,
                )
                return Response({"status": "ok", "note": "menu sent"}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                send_telegram_message(
                    chat_id,
                    f"Привет! Чтобы пользоваться функциями бота, вам нужно создать аккаунт на нашем сайте и "
                    f"привязать его, или войти в существующий и указать свой Telegram Chat ID ({chat_id}).",
                )
                return Response({"status": "ok", "note": "user not registered"}, status=status.HTTP_200_OK)

        if text == "/stop":
            try:
                user = User.objects.get(telegram_chat_id=chat_id)
                profile, _ = UserProfile.objects.get_or_create(user=user)
                profile.notify_telegram = False
                profile.save()
                send_telegram_message(chat_id, "Напоминания отключены. "
                                               "Чтобы снова получать — используйте /start.")
            except User.DoesNotExist:
                send_telegram_message(chat_id, "Вы не были зарегистрированы в системе.")
            except Exception as e:
                logger.error(f"Ошибка при отключении напоминаний через /stop: {e}")
                send_telegram_message(chat_id, "Ошибка при отключении напоминаний.")
            return Response({"status": "ok"})

        send_telegram_message(chat_id, "Я не понял вашу команду. Используйте /start для вызова меню.")
        return Response({"status": "ok", "note": "unhandled message"}, status=status.HTTP_200_OK)
