import datetime

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase
from django.utils import timezone

from users.middleware import LastActiveMiddleware
from users.models import User


class LastActiveMiddlewareTest(TestCase):
    """
    Тесты для LastActiveMiddleware, обеспечивающие 100% покрытие строк.
    """

    def setUp(self):
        """
        Настройка тестовых данных и объектов перед каждым тестом.
        """
        self.factory = RequestFactory()
        self.middleware = LastActiveMiddleware(self.get_response_mock)
        self.user = User.objects.create_user(email='test@example.com', password='password123')

    def get_response_mock(self, request):
        """
        Мок функция для `get_response`, имитирующая прохождение запроса.
        """
        return "OK"

    def test_authenticated_user_updates_last_active(self):
        """
        Проверяет, что `last_active` обновляется для аутентифицированного пользователя.
        """
        request = self.factory.get('/')
        request.user = self.user
        initial_last_active = self.user.last_active
        self.middleware(request)
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.last_active)
        self.assertGreater(self.user.last_active,
                           initial_last_active if initial_last_active else timezone.datetime(1970, 1, 1, tzinfo=timezone.get_current_timezone()))

        self.assertLess((timezone.now() - self.user.last_active).total_seconds(), 5)

    def test_unauthenticated_user_no_update(self):
        """
        Проверяет, что `last_active` не обновляется для неаутентифицированного пользователя.
        """
        request = self.factory.get('/')
        request.user = AnonymousUser()
        self.assertFalse(request.user.is_authenticated)
        initial_last_active = self.user.last_active
        self.middleware(request)
        self.user.refresh_from_db()
        self.assertEqual(self.user.last_active, initial_last_active)

    def test_request_has_no_user_attribute(self):
        """
        Проверяет, что middleware корректно обрабатывает случай, когда у объекта request
        отсутствует атрибут `user`.
        """
        request = self.factory.get('/')
        with self.assertRaises(AttributeError):
            _ = request.user
        initial_last_active = self.user.last_active
        self.middleware(request)
        self.user.refresh_from_db()
        self.assertEqual(self.user.last_active, initial_last_active)