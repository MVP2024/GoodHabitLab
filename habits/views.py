from rest_framework import viewsets, permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q
from drf_spectacular.utils import (
    extend_schema, OpenApiParameter, OpenApiResponse
)
import logging
from telegram_bot.tasks import send_habit_reminder, send_congratulation
from .models import Habit, HabitCategory, HabitLog, Reward, Notification
from .serializers import (
    HabitSerializer, HabitCategorySerializer, HabitLogSerializer, RewardSerializer, NotificationSerializer
)


@extend_schema(
    summary="Управление привычками пользователя",
    tags=["Привычки"],
)
class HabitViewSet(viewsets.ModelViewSet):
    """
    Управление привычками пользователя.
    """
    serializer_class = HabitSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        return Habit.objects.filter(
            Q(user=self.request.user) | Q(is_public=True),
            is_active=True
        ).order_by('id')

    @extend_schema(
        summary="Получить список привычек",
        description="Возвращает список всех привычек текущего пользователя, "
                    "а также публичных привычек других пользователей.",
        tags=["Привычки"],
        responses=HabitSerializer(many=True),
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Получить информацию о привычке",
        description="Получить подробную информацию о привычке по её ID (если она доступна пользователю).",
        tags=["Привычки"],
        parameters=[OpenApiParameter("id", int, OpenApiParameter.PATH, description="ID привычки")],
        responses=HabitSerializer,
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Создать новую привычку",
        description="Создает новую привычку, автоматически привязывая её к текущему пользователю.",
        tags=["Привычки"],
        request=HabitSerializer,
        responses=HabitSerializer,
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary="Обновить привычку целиком",
        description="Полностью обновить данные выбранной привычки пользователя по её ID.",
        tags=["Привычки"],
        parameters=[OpenApiParameter("id", int, OpenApiParameter.PATH, description="ID привычки")],
        request=HabitSerializer,
        responses=HabitSerializer,
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary="Частично обновить привычку",
        description="Частично изменить указанные поля привычки пользователя по её ID.",
        tags=["Привычки"],
        parameters=[OpenApiParameter("id", int, OpenApiParameter.PATH, description="ID привычки")],
        request=HabitSerializer,
        responses=HabitSerializer,
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        summary="Удалить привычку",
        description="Удаляет выбранную привычку пользователя по её ID (если у вас есть доступ).",
        tags=["Привычки"],
        parameters=[OpenApiParameter("id", int, OpenApiParameter.PATH, description="ID привычки")],
        responses={204: OpenApiResponse(description="Успешное удаление привычки")},
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], url_path='copy')
    @extend_schema(
        summary="Скопировать публичную привычку",
        description="Создает личную копию выбранной публичной привычки для текущего пользователя.",
        tags=["Привычки"],
        responses={
            201: HabitSerializer,
            400: OpenApiResponse(description="Привычка не найдена или не является публичной."),
        },
    )
    def copy(self, request, pk=None):
        try:
            original_habit = self.get_queryset().get(pk=pk, is_public=True)
        except Habit.DoesNotExist:
            return Response(
                {"detail": "Привычка не найдена или не является публичной."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Создаем новую привычку на основе существующей
        new_habit_data = {
            'title': original_habit.title,
            'description': original_habit.description,
            'category': original_habit.category.id if original_habit.category else None,
            'is_public': False,  # Копированная привычка всегда личная
            'periodicity': original_habit.periodicity,
            'selected_weekdays': original_habit.selected_weekdays,
            'place': original_habit.place,
            'color': original_habit.color,
            'icon': original_habit.icon,
            'is_active': True,
            'planned_time': original_habit.planned_time,
            'is_pleasant': original_habit.is_pleasant,
            'duration': original_habit.duration,
            'reward': original_habit.reward,
            'related_habit': original_habit.related_habit.id if original_habit.related_habit else None,

        }

        serializer = self.get_serializer(data=new_habit_data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=self.request.user)  # Привязываем к текущему пользователю

        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["Категории привычек"],
    summary="Работа с категориями привычек"
)
class HabitCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления категориями привычек.

    Позволяет создавать, изменять, удалять и просматривать категории.
    """
    queryset = HabitCategory.objects.all().order_by('id')
    serializer_class = HabitCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    @extend_schema(
        summary="Получить список категорий привычек",
        description="Возвращает список всех категорий привычек.",
        tags=["Категории привычек"],
        responses=HabitCategorySerializer(many=True),
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Создать новую категорию привычек",
        description="Создает новую категорию привычек.",
        tags=["Категории привычек"],
        request=HabitCategorySerializer,
        responses=HabitCategorySerializer,
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary="Получить информацию о категории",
        description="Получить подробную информацию о категории привычек по её ID.",
        tags=["Категории привычек"],
        parameters=[OpenApiParameter("id", int, OpenApiParameter.PATH, description="ID категории")],
        responses=HabitCategorySerializer,
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Обновить категорию привычек целиком",
        description="Полностью обновить данные выбранной категории по её ID.",
        tags=["Категории привычек"],
        parameters=[OpenApiParameter("id", int, OpenApiParameter.PATH, description="ID категории")],
        request=HabitCategorySerializer,
        responses=HabitCategorySerializer,
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary="Частично обновить категорию привычек",
        description="Частично изменить указанные поля категории по её ID.",
        tags=["Категории привычек"],
        parameters=[OpenApiParameter("id", int, OpenApiParameter.PATH, description="ID категории")],
        request=HabitCategorySerializer,
        responses=HabitCategorySerializer,
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        summary="Удалить категорию привычек",
        description="Удаляет выбранную категорию по её ID.",
        tags=["Категории привычек"],
        parameters=[OpenApiParameter("id", int, OpenApiParameter.PATH, description="ID категории")],
        responses={204: OpenApiResponse(description="Успешное удаление категории")},
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


@extend_schema(
    tags=["Логи привычек"],
    summary="История выполнения привычек"
)
class HabitLogViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с логами (историей выполнения) привычек.

    Позволяет получать список выполнений, создавать новые записи выполнения привычки, смотреть детали.
    """
    queryset = HabitLog.objects.all()
    serializer_class = HabitLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        return HabitLog.objects.filter(habit__user=self.request.user).order_by('id')

    @extend_schema(
        summary="Получить список логов привычек",
        description="Возвращает список всех записей выполнения привычек (логов).",
        tags=["Логи привычек"],
        responses=HabitLogSerializer(many=True),
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Создать лог привычки",
        description="Создает новую запись лога (выполнения привычки).",
        tags=["Логи привычек"],
        request=HabitLogSerializer,
        responses=HabitLogSerializer,
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary="Получить детальный лог привычки",
        description="Получить подробную информацию о конкретном логе привычки по ID.",
        tags=["Логи привычек"],
        parameters=[OpenApiParameter("id", int, OpenApiParameter.PATH, description="ID лога")],
        responses=HabitLogSerializer,
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Обновить лог привычки целиком",
        description="Полностью обновить данные лог-записи по её ID.",
        tags=["Логи привычек"],
        parameters=[OpenApiParameter("id", int, OpenApiParameter.PATH, description="ID лога")],
        request=HabitLogSerializer,
        responses=HabitLogSerializer,
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary="Частично обновить лог привычки",
        description="Частично изменить указанные поля лог-записи по её ID.",
        tags=["Логи привычек"],
        parameters=[OpenApiParameter("id", int, OpenApiParameter.PATH, description="ID лога")],
        request=HabitLogSerializer,
        responses=HabitLogSerializer,
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        summary="Удалить лог привычки",
        description="Удалить выбранный лог привычки по его ID.",
        tags=["Логи привычек"],
        parameters=[OpenApiParameter("id", int, OpenApiParameter.PATH, description="ID лога")],
        responses={204: OpenApiResponse(description="Успешное удаление лог-записи")},
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def perform_create(self, serializer):
        habit_log = serializer.save(user=self.request.user)
        user = habit_log.habit.user  # Получаем пользователя из привычки
        chat_id = getattr(user, "telegram_chat_id", None)
        profile = getattr(user, "userprofile", None)  # Получаем профиль пользователя

        if chat_id:
            if profile and not profile.notify_telegram:
                # Добавляем логирование, если уведомления в Telegram отключены
                logging.info(f"Уведомления для пользователя {user.email} в Telegram отключены в профиле.")
                return

            if habit_log.is_done:
                send_congratulation.delay(
                    str(chat_id),
                    f"Поздравляем! Вы выполнили привычку: {habit_log.habit.title}!"
                )
            else:
                send_habit_reminder.delay(
                    str(chat_id),
                    f"Вы забыли выполнить привычку: {habit_log.habit.title}"
                )
        else:
            logging.warning(f"У пользователя {user.email} отсутствует telegram_chat_id, уведомление не отправлено.")


@extend_schema(
    tags=["Награды"],
    summary="Управление наградами за привычки"
)
class RewardViewSet(viewsets.ModelViewSet):
    """
    ViewSet для моделирования и отслеживания наград за выполнение привычек.
    """
    serializer_class = RewardSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        return Reward.objects.filter(habit__user=self.request.user).order_by('id')

    @extend_schema(
        summary="Получить список наград за привычки",
        description="Возвращает список всех наград, связанных с привычками пользователя.",
        tags=["Награды"],
        responses=RewardSerializer(many=True),
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Создать новую награду",
        description="Создает новую награду за выполнение привычки.",
        tags=["Награды"],
        request=RewardSerializer,
        responses=RewardSerializer,
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary="Получить детальную информацию о награде",
        description="Получить подробную информацию о награде за привычку по её ID.",
        tags=["Награды"],
        parameters=[OpenApiParameter("id", int, OpenApiParameter.PATH, description="ID награды")],
        responses=RewardSerializer,
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Обновить награду целиком",
        description="Полностью обновить данные выбранной награды по её ID.",
        tags=["Награды"],
        parameters=[OpenApiParameter("id", int, OpenApiParameter.PATH, description="ID награды")],
        request=RewardSerializer,
        responses=RewardSerializer,
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary="Частично обновить награду",
        description="Частично изменить указанные поля награды по её ID.",
        tags=["Награды"],
        parameters=[OpenApiParameter("id", int, OpenApiParameter.PATH, description="ID награды")],
        request=RewardSerializer,
        responses=RewardSerializer,
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        summary="Удалить награду",
        description="Удаляет выбранную награду по её ID.",
        tags=["Награды"],
        parameters=[OpenApiParameter("id", int, OpenApiParameter.PATH, description="ID награды")],
        responses={204: OpenApiResponse(description="Успешное удаление награды")},
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def perform_create(self, serializer):
        habit = serializer.validated_data['habit']
        serializer.save(user=habit.user)


@extend_schema(
    tags=["Уведомления"],
    summary="Просмотр истории отправленных уведомлений"
)
class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Только для чтения (ReadOnlyModelViewSet), чтобы просматривать историю отправленных уведомлений пользователю.

    Можно получить список или подробную информацию об уведомлении.
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('id')

    @extend_schema(
        summary="Получить список отправленных уведомлений",
        description="Возвращает список всех уведомлений, которые были отправлены текущему пользователю.",
        tags=["Уведомления"],
        responses=NotificationSerializer(many=True),
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Получить детали уведомления",
        description="Возвращает детали одного уведомления по его ID.",
        tags=["Уведомления"],
        parameters=[OpenApiParameter("id", int, OpenApiParameter.PATH, description="ID уведомления")],
        responses=NotificationSerializer,
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def perform_create(self, serializer):
        user = self.request.user
        habit = serializer.validated_data.get('habit')
        notification_type = serializer.validated_data.get('notification_type', 'info')  # По умолчанию 'info'

        message = serializer.validated_data.get('message')

        # Если сообщение не предоставлено, генерируем его на основе типа
        if not message:
            if notification_type == 'reminder' and habit:
                message = f"Напоминание: пора выполнить привычку '{habit.title}'!"
            elif notification_type == 'congratulation' and habit:
                message = f"Поздравляем! Вы успешно выполнили привычку '{habit.title}'!"
            elif notification_type == 'info':
                message = "У вас есть новое информационное сообщение."
            elif notification_type == 'warning':
                message = "Важное предупреждение! Обратите внимание на ваши привычки."
            elif notification_type == 'inactive_reminder':
                message = "Мы заметили, что вы давно не выполняли привычки. Пора вернуться к ним!"
            else:
                message = ("Внутренняя ошибка: Не удалось сформировать сообщение уведомления. "
                           "Пожалуйста, обратитесь в поддержку.")

        serializer.save(user=user, message=message, notification_type=notification_type)
