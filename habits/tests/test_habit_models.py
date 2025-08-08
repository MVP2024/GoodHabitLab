from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from habits.models import (DailyHabitLog, Habit, HabitCategory, HabitLog,
                           HabitTracking, Notification, Reward)
from users.models import User


class HabitModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(email='testuser@example.com')
        self.category = HabitCategory.objects.create(
            name='Здоровье',
            description='Привычки, связанные со здоровьем'
        )
        self.habit = Habit.objects.create(
            user=self.user,
            title='Утренняя пробежка',
            description='Бегать 30 минут каждое утро',
            category=self.category,
            is_public=True,
            periodicity='daily',
            place='Парк',
            duration=60,
            is_pleasant=False,
            reward='Съесть яблоко'
        )
        self.pleasant_habit = Habit.objects.create(
            user=self.user,
            title='Медитация',
            description='Медитировать 10 минут',
            is_public=False,
            periodicity='daily',
            place='Дом',
            duration=10,
            is_pleasant=True
        )

    def test_habit_str_representation(self):
        expected = f"{self.user} - Утренняя пробежка"
        self.assertEqual(str(self.habit), expected)

    def test_clean_habit_with_both_reward_and_related_habit(self):
        habit = Habit(
            user=self.user,
            title='Пить воду',
            duration=30,
            reward='Выпить кофе',
            related_habit=self.pleasant_habit
        )
        with self.assertRaises(ValidationError) as context:
            habit.clean()
        self.assertIn(
            "Нельзя одновременно выбирать связанную привычку и указывать вознаграждение.",
            str(context.exception)
        )

    def test_clean_habit_duration_too_long(self):
        habit = Habit(
            user=self.user,
            title='Читать книгу',
            duration=150,
            reward='Посмотреть сериал'
        )
        with self.assertRaises(ValidationError) as context:
            habit.clean()
        self.assertIn(
            "Время выполнения привычки не должно превышать 120 секунд.",
            str(context.exception)
        )

    def test_clean_invalid_related_habit(self):
        habit = Habit(
            user=self.user,
            title='Йога',
            duration=60,
            related_habit=self.habit  # Не приятная привычка
        )
        with self.assertRaises(ValidationError) as context:
            habit.clean()
        self.assertIn(
            "В связанные привычки могут быть добавлены только приятные привычки.",
            str(context.exception)
        )

    def test_clean_pleasant_habit_with_reward(self):
        habit = Habit(
            user=self.user,
            title='Слушать музыку',
            duration=20,
            is_pleasant=True,
            reward='Полакомиться шоколадом'
        )
        with self.assertRaises(ValidationError) as context:
            habit.clean()
        self.assertIn(
            "У приятной привычки не может быть вознаграждения.",
            str(context.exception)
        )

    def test_clean_pleasant_habit_with_related_habit(self):
        habit = Habit(
            user=self.user,
            title='Гулять с собакой',
            duration=40,
            is_pleasant=True,
            related_habit=self.pleasant_habit
        )
        with self.assertRaises(ValidationError) as context:
            habit.clean()
        self.assertIn(
            "У приятной привычки не может быть связанной привычки.",
            str(context.exception)
        )

    def test_clean_custom_periodicity_without_weekdays(self):
        habit = Habit(
            user=self.user,
            title='Занятия спортом',
            duration=45,
            periodicity='custom',
            place='Спортзал'
        )
        with self.assertRaises(ValidationError) as context:
            habit.full_clean()  # Используем full_clean для вызова clean() и валидации полей
        self.assertIn(
            "Для 'Выборочных дней' необходимо выбрать хотя бы один день недели.",
            context.exception.message_dict['selected_weekdays'][0]
        )



class HabitLogModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(email='testuser@example.com')
        self.habit = Habit.objects.create(
            user=self.user,
            title='Чистка зубов',
            place='В ванной',
            duration=120
        )

    def test_habit_log_str_representation(self):
        log = HabitLog.objects.create(
            habit=self.habit,
            user=self.user,
            date=timezone.now().date(),
            is_done=True
        )
        expected = f"{self.habit} - {log.date}: Выполнено"
        self.assertEqual(str(log), expected)


class DailyHabitLogModelTest(TestCase):
    def test_daily_habit_log_unique_together(self):
        user = User.objects.create(email='dailytest@example.com')
        habit = Habit.objects.create(user=user, title='Тест ежедневного лога', place='Дом', duration=30)
        date = timezone.now().date()

        log1 = DailyHabitLog.objects.create(habit=habit, user=user, date=date, status='done')
        self.assertEqual(log1.status, 'done')

        # Проверяем уникальность
        with self.assertRaises(Exception):
            DailyHabitLog.objects.create(habit=habit, user=user, date=date, status='skipped')


class RewardModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(email='rewarduser@example.com')
        self.habit = Habit.objects.create(user=self.user, title='Изучение языка', place='Дом', duration=30)

    def test_reward_str_representation(self):
        reward = Reward.objects.create(
            habit=self.habit,
            user=self.user,
            description='Посмотреть фильм на изучаемом языке'
        )
        expected = f"Награда за «{self.habit.title}»: Посмотреть фильм на изучаемом языке"
        self.assertEqual(str(reward), expected)


class HabitTrackingModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(email='trackinguser@example.com')
        self.habit = Habit.objects.create(user=self.user, title='Не пить сладкое', place='Кухня', duration=30)

    def test_habit_tracking_str_representation(self):
        tracking = HabitTracking.objects.create(
            habit=self.habit,
            user=self.user,
            start_date=timezone.now().date(),
            status='in_progress',
            progress=50
        )
        expected = f"{self.user} - {self.habit.title} ({tracking.status})"
        self.assertEqual(str(tracking), expected)



class NotificationModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(email='notifyuser@example.com')
        self.habit = Habit.objects.create(user=self.user, title='Выпивать 2 литра воды', place='Офис', duration=30)

    def test_notification_str_representation(self):
        notification = Notification.objects.create(
            user=self.user,
            habit=self.habit,
            message='Не забудьте выпить воды!',
            channel='telegram',
            notification_type='reminder'
        )
        # Создаем корректный формат строки без миллисекунд
        sent_at_formatted = notification.sent_at.strftime('%d.%m.%Y %H:%M')
        expected = f"[{sent_at_formatted}] {self.user.username}: Не забудьте выпить вод..."
        self.assertEqual(str(notification)[:len(expected) - 3], expected[:len(expected) - 3])
