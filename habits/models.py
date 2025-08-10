from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models

from users.models import User


class HabitCategory(models.Model):
    """
    Категория привычки для удобной группировки, поиска и статистики.
    """
    name: str = models.CharField(
        max_length=100, unique=True, verbose_name="Название категории"
    )
    description: str = models.TextField(
        blank=True, null=True, verbose_name="Описание категории"
    )

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = "Категория привычки"
        verbose_name_plural = "Категории привычек"


class Habit(models.Model):
    """
        Модель, представляющая привычку пользователя.
        Определяет такие характеристики, как действие, время, место, периодичность,
        связанные вознаграждения или приятные привычки.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='habits', verbose_name='Пользователь')
    title = models.CharField(max_length=255, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    category = models.ForeignKey('HabitCategory', on_delete=models.SET_NULL, null=True, blank=True,
                                 verbose_name="Категория")
    is_public = models.BooleanField(default=False, verbose_name="Публичная привычка")
    periodicity = models.CharField(
        max_length=50,
        default='daily',
        choices=[
            ('daily', 'Ежедневно'),
            ('custom', 'Выборочные дни')
        ],
        verbose_name="Периодичность"
    )
    # Используем ArrayField для хранения списка дней недели
    selected_weekdays: list[str] = ArrayField(
        models.CharField(max_length=10),
        blank=True,
        default=list,
        verbose_name="Выбранные дни недели (например, ['пн', 'ср', 'пт'])"
    )
    place: str = models.CharField(max_length=255, verbose_name="Место выполнения привычки",
                                  help_text="Место, в котором необходимо выполнять привычку.")
    color = models.CharField(max_length=7, blank=True, verbose_name="Цвет")
    icon = models.CharField(max_length=30, blank=True, verbose_name="Иконка")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата последнего обновления")
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    planned_time = models.TimeField(null=True, blank=True, verbose_name="Плановое время")
    is_pleasant = models.BooleanField(default=False, verbose_name="Приятная привычка")
    duration = models.PositiveSmallIntegerField(
        verbose_name="Время на выполнение (секунды)",
        help_text="Время, которое предположительно потратит пользователь на выполнение привычки (не более 120 секунд)"
    )
    reward = models.CharField(
        max_length=255, blank=True, null=True,
        verbose_name="Вознаграждение",
        help_text="Чем пользователь должен себя вознаградить после выполнения (текстовое описание)"
    )
    related_habit = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='useful_habits', verbose_name="Привычка",
        help_text="Привычка, которая связана с другой привычкой (должна быть приятной привычкой)"
    )

    def __str__(self) -> str:
        return f"{self.user} - {self.title}"

    def _validate_reward_and_related_habit(self) -> None:
        """Валидация 1: Исключить одновременный выбор связанной привычки и вознаграждения."""
        if self.related_habit and self.reward:
            raise ValidationError(
                "Нельзя одновременно выбирать связанную привычку и указывать вознаграждение.",
                code='non_field_errors'
            )

    def _validate_duration(self) -> None:
        """Валидация 2: Время выполнения должно быть не больше 120 секунд."""
        if self.duration and self.duration > 120:
            raise ValidationError(
                {"duration": "Время выполнения привычки не должно превышать 120 секунд."}
            )

    def _validate_related_habit_is_pleasant(self) -> None:
        """Валидация 3: В связанные привычки могут попадать только приятные привычки."""
        if self.related_habit and not self.related_habit.is_pleasant:
            raise ValidationError(
                "В связанные привычки могут быть добавлены только приятные привычки.",
                code='non_field_errors'
            )

    def _validate_pleasant_habit_constraints(self) -> None:
        """Валидация 4: У приятной привычки не может быть вознаграждения или связанной привычки."""
        if self.is_pleasant:
            if self.reward:
                raise ValidationError(
                    "У приятной привычки не может быть вознаграждения.",
                    code='non_field_errors'
                )
            if self.related_habit:
                raise ValidationError(
                    "У приятной привычки не может быть связанной привычки.",
                    code='non_field_errors'
                )

    def _validate_custom_periodicity(self) -> None:
        """
        Валидация 5: Для выборочной периодичности должен быть выбран хотя бы один день и проверка на реже
        чем 1 раза в 7 дней.
        Включает также логику трансформации данных.
        """
        all_weekdays_keys = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс']

        if self.periodicity == 'daily':
            # Если 'daily', принудительно устанавливаем все дни недели
            self.selected_weekdays = all_weekdays_keys
        elif self.periodicity == 'custom':
            if not self.selected_weekdays:
                raise ValidationError(
                    {"selected_weekdays": "Для 'Выборочных дней' необходимо выбрать хотя бы один день недели."}
                )

            # Проверка на то, что custom с всеми днями должен быть daily, и изменение
            if set(self.selected_weekdays) == set(all_weekdays_keys):
                self.periodicity = 'daily'
                self.selected_weekdays = all_weekdays_keys  # Убеждаемся, что дни останутся полными
            else:
                # Убираем дубликаты дней недели и проверяем на наличие некорректных дней
                unique_weekdays = sorted(set(self.selected_weekdays),
                                         key=lambda x: all_weekdays_keys.index(x) if x in all_weekdays_keys else -1)

                if any(day not in all_weekdays_keys for day in unique_weekdays):
                    raise ValidationError(
                        {
                            "selected_weekdays": f"Некорректные дни недели: {unique_weekdays}."
                                                 f" Допустимые значения: {all_weekdays_keys}"}
                    )
                self.selected_weekdays = unique_weekdays

                weekdays_order = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс']
                selected_indices = []
                for day in self.selected_weekdays:
                    try:
                        selected_indices.append(weekdays_order.index(day))
                    except ValueError:
                        # Обработка случая, если в selected_weekdays попал невалидный день
                        # Это должно быть уже поймано выше, но на всякий случай
                        raise ValidationError(f"Некорректное значение дня недели: '{day}'.")
                selected_indices.sort()

                if not selected_indices:  # Если после удаления дубликатов список стал пустым
                    raise ValidationError(
                        {"selected_weekdays": "Для 'Выборочных дней' необходимо выбрать хотя бы один день недели."}
                    )

                # Проверяем, что привычка выполняется хотя бы 1 раз в 7 дней.
                max_gap = 0

                if len(selected_indices) == 1:
                    max_gap = 6
                else:
                    extended_indices = selected_indices + [selected_indices[0] + 7]

                    for i in range(len(selected_indices)):
                        gap = extended_indices[i + 1] - extended_indices[i] - 1
                        if gap > max_gap:
                            max_gap = gap

                if max_gap >= 7:
                    raise ValidationError(
                        "Нельзя выполнять привычку реже, чем 1 раз в 7 дней. "
                        "Выберите дни так, чтобы привычка выполнялась хотя бы один раз в неделю."
                    )
        else:
            # Если periodicity не 'daily' и не 'custom', очищаем selected_weekdays
            self.selected_weekdays = []

    def clean(self) -> None:
        """
        Метод для выполнения комплексной валидации полей модели Habit.
        Переопределяет стандартный метод `clean` Django.
        """
        self._validate_reward_and_related_habit()
        self._validate_duration()
        self._validate_related_habit_is_pleasant()
        self._validate_pleasant_habit_constraints()
        self._validate_custom_periodicity()

    class Meta:
        verbose_name = 'Привычка'
        verbose_name_plural = 'Привычки'


class HabitLog(models.Model):
    """
    История выполнения привычки пользователем (для streak'ов и статистики).
    """

    habit: models.ForeignKey = models.ForeignKey(
        Habit,
        on_delete=models.CASCADE,
        related_name='logs',
        verbose_name='Привычка',
    )
    date: models.DateField = models.DateField(verbose_name="Дата выполнения")
    is_done: models.BooleanField = models.BooleanField(default=True, verbose_name="Выполнено")
    user: User = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="habit_logs",
        verbose_name="Пользователь",
    )
    last_reminded_at = models.DateTimeField(null=True, blank=True, verbose_name="Время последнего напоминания")

    def __str__(self) -> str:
        return f"{self.habit} - {self.date}: {'Выполнено' if self.is_done else 'Не выполнено'}"

    class Meta:
        verbose_name = "Лог привычки"
        verbose_name_plural = "Логи привычек"
        unique_together = ("habit", "date")


class DailyHabitLog(models.Model):
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE, related_name='daily_logs', verbose_name='Привычка')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_habit_logs',
                             verbose_name='Пользователь')
    date = models.DateField(verbose_name="Дата")
    status = models.CharField(max_length=20, choices=[('done', 'Выполнено'), ('skipped', 'Пропущено')], default='done',
                              verbose_name='Статус')
    note = models.CharField(max_length=255, blank=True, verbose_name='Примечание')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    time_completed = models.TimeField(null=True, blank=True, verbose_name='Время выполнения')

    class Meta:
        verbose_name = "Ежедневный лог привычки"
        verbose_name_plural = "Ежедневные логи привычек"
        unique_together = ('habit', 'date')


class Reward(models.Model):
    """
    Модель вознаграждения.
    Определяет свойства и валидацию для каждого вознаграждения.
    """
    habit: models.ForeignKey = models.ForeignKey(
        Habit,
        on_delete=models.CASCADE,
        related_name='rewards',
        verbose_name='Привычка',
    )
    description: str = models.CharField(max_length=255, verbose_name="Описание награды")
    created_at: models.DateTimeField = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    updated_at: models.DateTimeField = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата последнего обновления"
    )
    user: User = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="rewards",
        verbose_name="Пользователь",
    )

    def __str__(self) -> str:
        return f"Награда за «{self.habit.title}»: {self.description}"

    class Meta:
        verbose_name = "Награда"
        verbose_name_plural = "Награды"


class HabitTracking(models.Model):
    """
        Модель для отслеживания прогресса выполнения привычек.
    """
    habit: models.ForeignKey = models.ForeignKey(Habit, on_delete=models.CASCADE, related_name='trackings',
                                                 verbose_name="Привычка")
    user: models.ForeignKey = models.ForeignKey(User, on_delete=models.CASCADE, related_name='habit_trackings',
                                                verbose_name="Пользователь")
    start_date: models.DateField = models.DateField(verbose_name="Дата начала")
    end_date: models.DateField = models.DateField(null=True, blank=True, verbose_name="Дата окончания")
    status: str = models.CharField(
        max_length=50,
        choices=[('in_progress', 'В процессе'), ('success', 'Успех'), ('fail', 'Неуспех'), ('paused', 'Пауза')],
        default='in_progress',
        verbose_name="Статус"
    )
    progress: int = models.PositiveIntegerField(default=0, verbose_name="Прогресс (%)")
    note: str = models.TextField(blank=True, verbose_name="Примечание")
    reason: str = models.TextField(blank=True, verbose_name="Причина (неуспех, завершение и т.д.)")
    last_updated: models.DateTimeField = models.DateTimeField(auto_now=True, verbose_name="Последнее обновление")
    is_archived: bool = models.BooleanField(default=False, verbose_name="Архивирована")

    def __str__(self) -> str:
        return f"{self.user} - {self.habit.title} ({self.status})"

    class Meta:
        verbose_name = "Отслеживание привычки"
        verbose_name_plural = "Отслеживания привычек"


class Notification(models.Model):
    """
    Лог отправленных уведомлений пользователю (через Telegram, email и т.д.).
    """
    NOTIFICATION_TYPES = (
        ('reminder', 'Напоминание о привычке'),
        ('congratulation', 'Поздравление с выполнением'),
        ('info', 'Информационное сообщение'),
        ('warning', 'Предупреждение'),
        ('inactive_reminder', 'Напоминание о неактивности'),
    )

    user: models.ForeignKey = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications",
                                                verbose_name="Пользователь")
    habit: models.ForeignKey = models.ForeignKey(
        Habit,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='notifications',
        verbose_name="Привычка")
    message: str = models.TextField(verbose_name="Текст уведомления", blank=True, null=True)
    sent_at: models.DateTimeField = models.DateTimeField(auto_now_add=True, verbose_name="Дата отправки")
    channel: str = models.CharField(
        max_length=20, choices=[('telegram', 'Telegram'), ('email', 'Email')],
        verbose_name='Канал'
    )
    notification_type: str = models.CharField(
        max_length=20, choices=NOTIFICATION_TYPES, verbose_name="Тип уведомления", blank=True, null=True
    )
    notification_title: str = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Заголовок уведомления"
    )

    def __str__(self) -> str:
        return f"[{self.sent_at.strftime('%d.%m.%Y %H:%M')}] {self.user.username}: {self.message[:30]}..."

    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"
