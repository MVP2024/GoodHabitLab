from datetime import time

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from habits.models import Habit, HabitCategory

User = get_user_model()


class HabitViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='otherpass123'
        )
        self.category = HabitCategory.objects.create(
            name='ЗОЖ',
            description='Здоровый образ жизни'
        )
        self.habit = Habit.objects.create(
            user=self.user,
            title='Пить воду',
            description='Пить 2 литра воды в день',
            category=self.category,
            is_public=False,
            periodicity='daily',
            place='Дом',
            planned_time=time(14, 35),
            is_pleasant=False,
            duration=60,
        )
        self.public_habit = Habit.objects.create(
            user=self.other_user,
            title='Читать книги',
            description='Читать по 30 страниц ежедневно',
            category=self.category,
            is_public=True,
            periodicity='custom',
            selected_weekdays=['пн', 'ср', 'пт'],
            place='Библиотека',
            planned_time=time(19, 0),
            is_pleasant=True,
            duration=40,
        )

    def test_list_habits_authenticated(self):
        """Тест получения списка привычек аутентифицированным пользователем."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/habits/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Пользователь должен видеть свои привычки + публичные привычки других
        self.assertEqual(len(response.data['results']), 2)
        habit_titles = [habit['title'] for habit in response.data['results']]
        self.assertIn(self.habit.title, habit_titles)
        self.assertIn(self.public_habit.title, habit_titles)

    def test_list_habits_unauthenticated(self):
        """Тест получения списка привычек неаутентифицированным пользователем."""
        response = self.client.get('/api/v1/habits/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_own_habit(self):
        """Тест получения детальной информации о своей привычке."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/v1/habits/{self.habit.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.habit.title)
        self.assertEqual(response.data['description'], self.habit.description)

    def test_retrieve_public_habit(self):
        """Тест получения детальной информации о публичной привычке другого пользователя."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/v1/habits/{self.public_habit.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.public_habit.title)

    def test_retrieve_private_habit_of_other_user(self):
        """Тест попытки получения приватной привычки другого пользователя."""
        self.client.force_authenticate(user=self.user)

        private_habit = Habit.objects.create(
            user=self.other_user,
            title='Личная привычка',
            description='Только для меня',
            is_public=False,
            periodicity='daily',
            place='Работа',
            planned_time=time(10, 0),
            duration=30
        )

        response = self.client.get(f'/api/v1/habits/{private_habit.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_habit(self):
        """Тест создания новой привычки."""
        self.client.force_authenticate(user=self.user)
        data = {
            'title': 'Новая привычка',
            'description': 'Описание новой привычки',
            'category': self.category.id,
            'is_public': True,
            'periodicity': 'custom',
            'selected_weekdays': ['пн', 'чт', 'сб'],
            'place': 'Парк',
            'planned_time': '08:00:00',
            'duration': 90,
            'reward': 'Получить награду'
        }
        response = self.client.post('/api/v1/habits/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Habit.objects.count(), 3)
        self.assertEqual(response.data['title'], data['title'])
        self.assertEqual(response.data['user'], self.user.id)

    def test_update_habit(self):
        """Тест полного обновления своей привычки."""
        self.client.force_authenticate(user=self.user)
        data = {
            'title': 'Обновленная привычка',
            'description': 'Новое описание',
            'category': self.category.id,
            'is_public': True,
            'periodicity': 'daily',
            'place': 'Офис',
            'planned_time': '15:00:00',
            'duration': 120,
            'reward': 'Отдохнуть'
        }
        response = self.client.put(f'/api/v1/habits/{self.habit.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.habit.refresh_from_db()
        self.assertEqual(self.habit.title, data['title'])
        self.assertEqual(self.habit.description, data['description'])

    def test_partial_update_habit(self):
        """Тест частичного обновления своей привычки."""
        self.client.force_authenticate(user=self.user)
        data = {
            'description': 'Частично обновленное описание',
            'duration': 45
        }
        response = self.client.patch(f'/api/v1/habits/{self.habit.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.habit.refresh_from_db()
        self.assertEqual(self.habit.description, data['description'])
        self.assertEqual(self.habit.duration, data['duration'])
        self.assertEqual(self.habit.title, 'Пить воду')

    def test_delete_habit(self):
        """Тест удаления своей привычки."""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f'/api/v1/habits/{self.habit.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Habit.objects.filter(user=self.user).count(), 0)

    def test_copy_public_habit(self):
        """Тест копирования публичной привычки."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/v1/habits/{self.public_habit.id}/copy/')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Проверяем, что создана новая привычка
        copied_habit = Habit.objects.get(id=response.data['id'])
        self.assertEqual(copied_habit.user, self.user)
        self.assertFalse(copied_habit.is_public)
        self.assertEqual(copied_habit.title, self.public_habit.title)
        self.assertEqual(copied_habit.description, self.public_habit.description)
        self.assertEqual(copied_habit.periodicity, self.public_habit.periodicity)
        self.assertEqual(copied_habit.selected_weekdays, self.public_habit.selected_weekdays)

    def test_copy_non_public_habit(self):
        """Тест попытки копирования не публичной привычки."""
        self.client.force_authenticate(user=self.user)
        # Создаем приватную привычку другого пользователя
        private_habit = Habit.objects.create(
            user=self.other_user,
            title='Приватная привычка',
            description='Нельзя копировать',
            is_public=False,
            periodicity='daily',
            place='Гараж',
            planned_time=time(20, 0),
            duration=60
        )

        response = self.client.post(f'/api/v1/habits/{private_habit.id}/copy/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data['Детально'],
            'Привычка не найдена или не является публичной.'
        )

    def test_public_habits_list(self):
        """Тест получения списка публичных привычек."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/habits/public/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], self.public_habit.title)
        self.assertEqual(response.data['results'][0]['user'], self.other_user.id)

    def test_validation_error_reward_and_related_habit(self):
        """Тест ошибки валидации при указании награды и связанной привычки одновременно."""
        self.client.force_authenticate(user=self.user)

        pleasant_habit = Habit.objects.create(
            user=self.user,
            title='Приятная привычка',
            description='Для связывания',
            is_public=True,
            periodicity='daily',
            place='Дом',
            planned_time=time(10, 0),
            is_pleasant=True,
            duration=30
        )

        data = {
            'title': 'Тестовая привычка',
            'description': 'Описание',
            'category': self.category.id,
            'is_public': False,
            'periodicity': 'daily',
            'place': 'Дом',
            'planned_time': '11:00:00',
            'duration': 60,
            'reward': 'Поесть вкусняшку',
            'related_habit': pleasant_habit.id
        }

        response = self.client.post('/api/v1/habits/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('__all__', response.data) # Проверяем, что ошибка в __all__
        self.assertIn(
            'Нельзя одновременно выбирать связанную привычку и указывать вознаграждение.',
            response.data['__all__'][0] # Теперь это список в __all__
        )

    def test_validation_error_duration_too_long(self):
        """Тест ошибки валидации при слишком длительном времени выполнения привычки."""
        self.client.force_authenticate(user=self.user)
        data = {
            'title': 'Тестовая долгая привычка',
            'description': 'Описание',
            'category': self.category.id,
            'is_public': False,
            'periodicity': 'daily',
            'place': 'Дом',
            'planned_time': '11:00:00',
            'duration': 150  # Больше 120 секунд
        }

        response = self.client.post('/api/v1/habits/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('duration', response.data)
        self.assertIn(
            'Время выполнения привычки не должно превышать 120 секунд.',
            response.data['duration'][0]
        )

    def test_validation_error_related_habit_not_pleasant(self):
        """Тест ошибки валидации при выборе не приятной привычки как связанной."""
        self.client.force_authenticate(user=self.user)

        not_pleasant_habit = Habit.objects.create(
            user=self.user,
            title='Не приятная привычка',
            description='Для связывания',
            is_public=True,
            periodicity='daily',
            place='Дом',
            planned_time=time(10, 0),
            is_pleasant=False,
            duration=30
        )

        data = {
            'title': 'Тестовая привычка',
            'description': 'Описание',
            'category': self.category.id,
            'is_public': False,
            'periodicity': 'daily',
            'place': 'Дом',
            'planned_time': '11:00:00',
            'duration': 60,
            'related_habit': not_pleasant_habit.id
        }

        response = self.client.post('/api/v1/habits/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('__all__', response.data) # Проверяем, что ошибка в __all__
        self.assertIn(
            'В связанные привычки могут быть добавлены только приятные привычки.',
            response.data['__all__'][0] # Теперь это список в __all__
        )
