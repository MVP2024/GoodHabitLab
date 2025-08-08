from django.core.exceptions import ValidationError
from rest_framework import serializers

from users.models import User

from .models import Habit, HabitCategory, HabitLog, Notification, Reward

HABIT_TITLE_SOURCE = "habit.title"


class HabitCategorySerializer(serializers.ModelSerializer):
    """
    Сериализатор для категории привычки.
    """

    class Meta:
        model = HabitCategory
        fields = "__all__"
        extra_kwargs = {
            'name': {'error_messages': {
                'unique': 'Название категории с таким названием уже существует.'}}
        }


class HabitLogSerializer(serializers.ModelSerializer):
    """
        Сериализатор для логов (истории) выполнения привычки.
    """
    habit_name = serializers.CharField(source=HABIT_TITLE_SOURCE, read_only=True)

    class Meta:
        model = HabitLog
        fields = ["id", "habit", "habit_name", "date", "is_done"]
        read_only_fields = ["id", "habit_name", "user"]


class RewardSerializer(serializers.ModelSerializer):
    """
    Сериализатор для вознаграждения.
    Используется для описания вознаграждения в привычке.
    """
    habit_title = serializers.CharField(source=HABIT_TITLE_SOURCE, read_only=True)

    class Meta:
        model = Reward
        fields = ["id", "habit", "habit_title", "description", "created_at"]
        read_only_fields = ["id", "habit_title", "created_at", "user"]


class NotificationSerializer(serializers.ModelSerializer):
    """
    Сериализатор для уведомлений.
    Используется для описания уведомлений в привычке.
    """
    user_email = serializers.CharField(source="user.email", read_only=True)
    habit_title = serializers.CharField(source=HABIT_TITLE_SOURCE, read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id",
            "user",
            "user_email",
            "habit",
            "habit_title",
            "message",
            "sent_at",
            "channel",
            "notification_type",
            "notification_title",
        ]
        read_only_fields = ["id", "user_email", "habit_title", "sent_at"]
        extra_kwargs = {
            'message': {'required': False},
            'notification_type': {'required': False},
            'notification_title': {'required': False}
        }


class HabitSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())
    category = serializers.PrimaryKeyRelatedField(queryset=HabitCategory.objects.all(), allow_null=True, required=False)
    related_habit = serializers.PrimaryKeyRelatedField(
        queryset=Habit.objects.all(), allow_null=True, required=False
    )

    """
    Сериализатор для модели привычки.
    Обеспечивает валидацию данных перед созданием или обновлением привычки.
    """

    class Meta:
        model = Habit
        fields = "__all__"
        read_only_fields = [
            "user"
        ]  # Поле user устанавливается автоматически при создании

    def validate(self, data: dict) -> dict:
        """
        Валидация данных для создания или обновления привычки.
        :param data:
        :return:
        """
        # Создаем временный экземпляр привычки с данными для валидации
        # или обновляем существующий, чтобы вызвать clean() модели.
        # Это важно для доступа к связанным объектам, таким как related_habit.
        if self.instance:
            # Обновляем существующий экземпляр для валидации
            temp_habit = self.instance
            for attr, value in data.items():
                setattr(temp_habit, attr, value)
        else:
            # Создаем новый экземпляр для валидации
            temp_habit = Habit(**data)
            # Временно устанавливаем пользователя, чтобы пройти валидацию модели
            # Добавлено условие, чтобы избежать ошибки, если request.user анонимный или отсутствует
            # (например, в тестах без аутентификации)
            if 'request' in self.context and self.context['request'].user.is_authenticated:
                temp_habit.user = self.context['request'].user
            elif 'user' in data and data['user'] is not None:  # Если user передан явно в данных
                # (например, для админа или тестов)
                try:
                    # Получаем объект User по ID
                    temp_habit.user = User.objects.get(id=data['user'])
                except User.DoesNotExist:
                    raise serializers.ValidationError({"user": "Указанный пользователь не существует."})
            else:
                # Если user не установлен, и это новый объект, raise ValidationError
                raise serializers.ValidationError({"user": "Пользователь не установлен для валидации привычки."})

        # Валидируем данные через метод clean() модели
        try:
            temp_habit.full_clean()  # full_clean вызывает clean, validate_constrains и validate_unique
        except ValidationError as e:
            # Перехватываем ошибки валидации модели и преобразуем их в ошибки сериализатора
            # e.message_dict содержит ошибки в виде {поле: [сообщение]}
            raise serializers.ValidationError(e.message_dict)

        return data
