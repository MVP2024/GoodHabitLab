from rest_framework import serializers

from .models import Habit, HabitCategory, HabitLog, Reward, Notification

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
                'unique': 'Категория привычки с таким названием уже существует. Пожалуйста, выберите другое название.'}}
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
            'message': {'required': False},  # Поле message теперь опционально при создании
            'notification_type': {'required': False},  # Поле notification_type тоже опционально
            'notification_title': {'required': False} # Поле notification_title тоже опционально
        }


class HabitSerializer(serializers.ModelSerializer):
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
        periodicity = data.get('periodicity')
        selected_weekdays = data.get('selected_weekdays')

        if periodicity == 'custom' and not selected_weekdays:
            raise serializers.ValidationError(
                {"selected_weekdays": "Для 'Выборочных дней' необходимо указать дни недели."}
            )
        # Если periodicity не 'custom', но selected_weekdays переданы, очищаем их
        if periodicity != 'custom' and selected_weekdays:
            data['selected_weekdays'] = []  # Устанавливаем пустой список

        # Валидация корректности дней недели (опционально, можно расширить)
        if periodicity == 'custom' and selected_weekdays:
            valid_days = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс']
            for day in selected_weekdays:
                if day.lower() not in valid_days:
                    raise serializers.ValidationError(
                        {
                            "selected_weekdays": f"Некорректный день недели: '{day}'. Используйте ['пн', 'вт', 'ср', ...]."}
                    )
        return data
