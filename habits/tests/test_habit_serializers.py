from datetime import date

from django.test import TestCase

from habits.models import Habit, HabitCategory, HabitLog, Notification, Reward
from habits.serializers import (HabitCategorySerializer, HabitLogSerializer,
                                HabitSerializer, NotificationSerializer,
                                RewardSerializer)
from users.models import User


# тесты для HabitCategorySerializer
class HabitCategorySerializerTest(TestCase):
    def setUp(self):
        self.category_data = {'name': 'Новая категория', 'description': 'Описание новой категории'}
        self.category = HabitCategory.objects.create(**self.category_data)
        self.serializer = HabitCategorySerializer(instance=self.category)

    def test_habit_category_serializer_contains_expected_fields(self):
        """
        Проверяет, что сериализатор содержит все ожидаемые поля.
        """
        data = self.serializer.data
        self.assertSetEqual(set(data.keys()), {'id', 'name', 'description'})

    def test_habit_category_serializer_name_field_content(self):
        """
        Проверяет содержимое поля 'name'.
        """
        data = self.serializer.data
        self.assertEqual(data['name'], self.category.name)

    def test_habit_category_serializer_description_field_content(self):
        """
        Проверяет содержимое поля 'description'.
        """
        data = self.serializer.data
        self.assertEqual(data['description'], self.category.description)

    def test_habit_category_serializer_create(self):
        """
        Проверяет создание новой категории через сериализатор.
        """
        new_category_data = {'name': 'Ещё одна категория', 'description': 'Описание ещё одной категории'}
        serializer = HabitCategorySerializer(data=new_category_data)
        self.assertTrue(serializer.is_valid())
        category_instance = serializer.save()
        self.assertIsInstance(category_instance, HabitCategory)
        self.assertEqual(category_instance.name, new_category_data['name'])
        self.assertEqual(category_instance.description, new_category_data['description'])
        self.assertEqual(HabitCategory.objects.count(), 2) # Проверяем, что создалась новая категория

    def test_habit_category_serializer_update(self):
        """
        Проверяет обновление существующей категории через сериализатор.
        """
        updated_data = {'name': 'Обновленная категория', 'description': 'Обновленное описание'}
        serializer = HabitCategorySerializer(instance=self.category, data=updated_data, partial=True)
        self.assertTrue(serializer.is_valid())
        category_instance = serializer.save()
        self.assertEqual(category_instance.name, updated_data['name'])
        self.assertEqual(category_instance.description, updated_data['description'])
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, updated_data['name'])


# тесты для HabitLogSerializer
class HabitLogSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', password='password123')
        self.category = HabitCategory.objects.create(name='Тестовая категория')
        self.habit = Habit.objects.create(
            user=self.user,
            title='Тестовая привычка',
            description='Описание тестовой привычки',
            category=self.category,
            periodicity='daily',
            place='Дом',
            duration=60,
            is_pleasant=False
        )
        self.habit_log_data = {
            'habit': self.habit.id,
            'date': date.today(),
            'is_done': True
        }
        self.habit_log = HabitLog.objects.create(
            habit=self.habit,
            user=self.user,
            date=date.today(),
            is_done=True
        )
        self.serializer = HabitLogSerializer(instance=self.habit_log)

    def test_habit_log_serializer_contains_expected_fields(self):
        """
        Проверяет, что сериализатор содержит все ожидаемые поля.
        """
        data = self.serializer.data
        self.assertSetEqual(set(data.keys()), {'id', 'habit', 'habit_name', 'date', 'is_done'})

    def test_habit_log_serializer_read_only_fields(self):
        """
        Проверяет, что поля 'id', 'habit_name', 'user' доступны только для чтения.
        """
        # Проверяем, что habit_name присутствует и соответствует ожидаемому значению
        self.assertIn('habit_name', self.serializer.data)
        self.assertEqual(self.serializer.data['habit_name'], self.habit.title)

        # Проверяем, что 'user' не может быть передан через data для создания/обновления
        # Это проверяется косвенно: если поле в read_only_fields, оно не должно быть в validated_data
        # при создании, если его явно не передают через save()
        new_habit_log_data_with_user = {
            'habit': self.habit.id,
            'date': date(2025, 8, 2),
            'is_done': False,
            'user': self.user.id # Попытка передать user, что должно быть проигнорировано
        }
        serializer = HabitLogSerializer(data=new_habit_log_data_with_user)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        # Убеждаемся, что 'user' не попал в validated_data, если он не был явно передан в save()
        self.assertNotIn('user', serializer.validated_data)

    def test_habit_log_serializer_create(self):
        """
        Проверяет создание нового лога привычки через сериализатор.
        """
        new_habit_log_data = {
            'habit': self.habit.id,
            'date': date(2025, 8, 1),
            'is_done': False
        }
        serializer = HabitLogSerializer(data=new_habit_log_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        # Передаем user через save(), как это обычно делается во ViewSet'ах
        habit_log_instance = serializer.save(user=self.user)
        self.assertIsInstance(habit_log_instance, HabitLog)
        self.assertEqual(habit_log_instance.habit, self.habit)
        self.assertEqual(habit_log_instance.date, new_habit_log_data['date'])
        self.assertEqual(habit_log_instance.is_done, new_habit_log_data['is_done'])
        self.assertEqual(habit_log_instance.user, self.user)

    def test_habit_log_serializer_update(self):
        """
        Проверяет обновление существующего лога привычки через сериализатор.
        """
        updated_data = {'is_done': False}
        serializer = HabitLogSerializer(instance=self.habit_log, data=updated_data, partial=True)
        self.assertTrue(serializer.is_valid())
        habit_log_instance = serializer.save()
        self.assertFalse(habit_log_instance.is_done)
        self.habit_log.refresh_from_db()
        self.assertFalse(self.habit_log.is_done)

    def test_habit_log_serializer_invalid_habit(self):
        """
        Проверяет валидацию с несуществующей привычкой.
        """
        invalid_data = {
            'habit': 999,  # Несуществующая привычка
            'date': date.today(),
            'is_done': True
        }
        serializer = HabitLogSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('habit', serializer.errors)
        self.assertEqual(str(serializer.errors['habit'][0]), 'Недопустимый первичный ключ "999" - объект не существует.')


# тесты для RewardSerializer
class RewardSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', password='password123')
        self.category = HabitCategory.objects.create(name='Тестовая категория')
        self.habit = Habit.objects.create(
            user=self.user,
            title='Тестовая привычка для вознаграждения',
            description='Описание тестовой привычки',
            category=self.category,
            periodicity='daily',
            place='Дом',
            duration=60,
            is_pleasant=False
        )
        self.reward_data = {
            'habit': self.habit.id,
            'description': 'Отличная награда'
        }
        self.reward = Reward.objects.create(
            habit=self.habit,
            user=self.user,
            description='Существующая награда'
        )
        self.serializer = RewardSerializer(instance=self.reward)

    def test_reward_serializer_contains_expected_fields(self):
        """
        Проверяет, что сериализатор содержит все ожидаемые поля.
        """
        data = self.serializer.data
        self.assertSetEqual(set(data.keys()), {'id', 'habit', 'habit_title', 'description', 'created_at'})

    def test_reward_serializer_read_only_fields(self):
        """
        Проверяет, что поля 'id', 'habit_title', 'created_at', 'user' доступны только для чтения.
        """
        data = self.serializer.data
        self.assertIn('habit_title', data)
        self.assertEqual(data['habit_title'], self.habit.title)
        self.assertIn('created_at', data)
        self.assertIsNotNone(data['created_at'])

        # Поле user не должно быть в валидированных данных, даже если передано
        invalid_update_data = {
            'description': 'Новое описание',
            'user': 9999 # Попытка изменить user
        }
        serializer = RewardSerializer(instance=self.reward, data=invalid_update_data, partial=True)
        self.assertTrue(serializer.is_valid())
        self.assertNotIn('user', serializer.validated_data)

    def test_reward_serializer_create(self):
        """
        Проверяет создание новой награды через сериализатор.
        """
        serializer = RewardSerializer(data=self.reward_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        reward_instance = serializer.save(user=self.user) # user передается через save()
        self.assertIsInstance(reward_instance, Reward)
        self.assertEqual(reward_instance.habit, self.habit)
        self.assertEqual(reward_instance.description, self.reward_data['description'])
        self.assertEqual(reward_instance.user, self.user)
        self.assertIsNotNone(reward_instance.created_at)

    def test_reward_serializer_update(self):
        """
        Проверяет обновление существующей награды через сериализатор.
        """
        updated_description = 'Обновленное описание награды'
        updated_data = {'description': updated_description}
        serializer = RewardSerializer(instance=self.reward, data=updated_data, partial=True)
        self.assertTrue(serializer.is_valid())
        reward_instance = serializer.save()
        self.assertEqual(reward_instance.description, updated_description)
        self.reward.refresh_from_db()
        self.assertEqual(self.reward.description, updated_description)

    def test_reward_serializer_invalid_habit(self):
        """
        Проверяет валидацию с несуществующей привычкой.
        """
        invalid_data = {
            'habit': 999,  # Несуществующая привычка
            'description': 'Несуществующая награда'
        }
        serializer = RewardSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('habit', serializer.errors)
        self.assertEqual(str(serializer.errors['habit'][0]), 'Недопустимый первичный ключ "999" - объект не существует.')


# тесты для NotificationSerializer
class NotificationSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', password='password123')
        self.habit = Habit.objects.create(
            user=self.user,
            title='Тестовая привычка для уведомлений',
            description='Описание тестовой привычки',
            periodicity='daily',
            place='Дом',
            duration=60,
            is_pleasant=False
        )
        self.notification_data = {
            'user': self.user.id,
            'habit': self.habit.id,
            'message': 'Тестовое сообщение уведомления',
            'channel': 'telegram',
            'notification_type': 'reminder',
            'notification_title': 'Напоминание'
        }
        self.notification = Notification.objects.create(
            user=self.user,
            habit=self.habit,
            message='Существующее уведомление',
            channel='email',
            notification_type='info',
            notification_title='Инфо'
        )
        self.serializer = NotificationSerializer(instance=self.notification)

    def test_notification_serializer_contains_expected_fields(self):
        """
        Проверяет, что сериализатор содержит все ожидаемые поля.
        """
        data = self.serializer.data
        expected_fields = {
            "id", "user", "user_email", "habit", "habit_title", "message",
            "sent_at", "channel", "notification_type", "notification_title"
        }
        self.assertSetEqual(set(data.keys()), expected_fields)

    def test_notification_serializer_read_only_fields(self):
        """
        Проверяет, что поля 'id', 'user_email', 'habit_title', 'sent_at' доступны только для чтения.
        """
        data = self.serializer.data
        self.assertIn('user_email', data)
        self.assertEqual(data['user_email'], self.user.email)
        self.assertIn('habit_title', data)
        self.assertEqual(data['habit_title'], self.habit.title)
        self.assertIn('sent_at', data)
        self.assertIsNotNone(data['sent_at'])

        # Попытка изменить read_only поле
        initial_user_email = data['user_email']
        update_data = {'user_email': 'new_email@example.com'}
        serializer = NotificationSerializer(instance=self.notification, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid())
        self.assertNotIn('user_email', serializer.validated_data)
        self.assertEqual(serializer.data['user_email'], initial_user_email)

    def test_notification_serializer_create(self):
        """
        Проверяет создание нового уведомления через сериализатор.
        """
        serializer = NotificationSerializer(data=self.notification_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        notification_instance = serializer.save()
        self.assertIsInstance(notification_instance, Notification)
        self.assertEqual(notification_instance.user, self.user)
        self.assertEqual(notification_instance.habit, self.habit)
        self.assertEqual(notification_instance.message, self.notification_data['message'])
        self.assertEqual(notification_instance.channel, self.notification_data['channel'])
        self.assertEqual(notification_instance.notification_type, self.notification_data['notification_type'])
        self.assertEqual(notification_instance.notification_title, self.notification_data['notification_title'])
        self.assertIsNotNone(notification_instance.sent_at)

    def test_notification_serializer_update(self):
        """
        Проверяет обновление существующего уведомления через сериализатор.
        """
        updated_message = 'Обновленное сообщение уведомления'
        updated_data = {'message': updated_message, 'channel': 'telegram'}
        serializer = NotificationSerializer(instance=self.notification, data=updated_data, partial=True)
        self.assertTrue(serializer.is_valid())
        notification_instance = serializer.save()
        self.assertEqual(notification_instance.message, updated_message)
        self.assertEqual(notification_instance.channel, 'telegram')
        self.notification.refresh_from_db()
        self.assertEqual(self.notification.message, updated_message)

    def test_notification_serializer_optional_fields(self):
        """
        Проверяет создание уведомления без необязательных полей.
        """
        minimal_data = {
            'user': self.user.id,
            'habit': self.habit.id,
            'channel': 'telegram',
            # message, notification_type, notification_title отсутствуют
        }
        serializer = NotificationSerializer(data=minimal_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        notification_instance = serializer.save()
        self.assertIsInstance(notification_instance, Notification)
        self.assertIsNone(notification_instance.message)
        self.assertIsNone(notification_instance.notification_type)
        self.assertIsNone(notification_instance.notification_title)

    def test_notification_serializer_invalid_user(self):
        """
        Проверяет валидацию с несуществующим пользователем.
        """
        invalid_data = self.notification_data.copy()
        invalid_data['user'] = 9999
        serializer = NotificationSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('user', serializer.errors)
        self.assertEqual(str(serializer.errors['user'][0]), 'Недопустимый первичный ключ "9999" - объект не существует.')

    def test_notification_serializer_invalid_habit(self):
        """
        Проверяет валидацию с несуществующей привычкой.
        """
        invalid_data = self.notification_data.copy()
        invalid_data['habit'] = 9999
        serializer = NotificationSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('habit', serializer.errors)
        self.assertEqual(str(serializer.errors['habit'][0]), 'Недопустимый первичный ключ "9999" - объект не существует.')