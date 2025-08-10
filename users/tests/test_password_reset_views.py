# users/tests/test_password_reset_views.py
import io
from unittest.mock import ANY, MagicMock, patch
from urllib.parse import urlsplit

from django.core import mail
from django.urls import include, path, resolve, reverse
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.test import APIRequestFactory, APITestCase

from users import urls
from users.models import User
from users.password_reset_views import APIRootView, CustomPasswordResetView
from users.serializers import (PasswordResetConfirmSerializer,
                               PasswordResetRequestSerializer)


# тесты для APIRootView
class APIRootViewTest(APITestCase):
    """
    Тесты для APIRootView.
    """

    @classmethod
    def setUpClass(cls): # Изменяем на setUpClass
        super().setUpClass()
        # Загружаем URLconf для приложения users
        cls.urlpatterns = 'users.urls' # Используем строковое представление URLconf

    def setUp(self):
        self.factory = APIRequestFactory()

    def test_get_serializer_class_for_password_reset(self):
        """
        Проверяет, что `get_serializer_class` возвращает `PasswordResetRequestSerializer`
        когда `url_name` равен "password_reset".
        """
        request = self.factory.post('/api/v1/users/password_reset/')
        # Имитируем resolver_match
        request.resolver_match = MagicMock()
        request.resolver_match.url_name = 'password_reset'

        view = APIRootView()
        view.request = request
        serializer_class = view.get_serializer_class()
        self.assertEqual(serializer_class, PasswordResetRequestSerializer)

    def test_get_serializer_class_for_password_reset_confirm(self):
        """
        Проверяет, что `get_serializer_class` возвращает `PasswordResetConfirmSerializer`
        когда `url_name` равен "password_reset_confirm".
        """
        # URLs для теста password_reset_confirm имеют параметры uid и token, которые resolve() ожидает
        # Создадим mock-ссылку, чтобы resolve() не пытался реально разобрать uid/token
        mock_url = '/api/v1/users/password_reset/confirm/uid/token/'
        request = self.factory.post(mock_url)
        # Имитируем resolver_match
        request.resolver_match = MagicMock()
        request.resolver_match.url_name = 'password_reset_confirm'

        view = APIRootView()
        view.request = request
        serializer_class = view.get_serializer_class()
        self.assertEqual(serializer_class, PasswordResetConfirmSerializer)

    def test_get_serializer_class_default(self):
        """
        Проверяет, что `get_serializer_class` возвращает `None`
        для неизвестного `url_name` (дефолтное поведение GenericAPIView).
        """
        request = self.factory.get('/some_other_url/')
        request.resolver_match = MagicMock(spec_set=['url_name']) # Мокаем только url_name
        request.resolver_match.url_name = 'some_other_name'

        view = APIRootView()
        view.request = request
        # Здесь мы должны убедиться, что super().get_serializer_class() вызывается
        # и возвращает ожидаемое значение (которое в данном случае None,
        # если APIRootView не имеет собственного serializer_class).
        # Для этого нужно мокнуть GenericAPIView.get_serializer_class.
        with patch('rest_framework.generics.GenericAPIView.get_serializer_class', return_value=None) as mock_super_get_serializer:
            serializer_class = view.get_serializer_class()
            self.assertIsNone(serializer_class)
            mock_super_get_serializer.assert_called_once()

    def test_authentication_classes(self):
        """
        Проверяет, что `authentication_classes` пустой.
        """
        view = APIRootView()
        self.assertEqual(view.authentication_classes, [])

    def test_permission_classes(self):
        """
        Проверяет, что `permission_classes` содержит `AllowAny`.
        """
        view = APIRootView()
        self.assertEqual(view.permission_classes, [AllowAny])


# тесты для CustomPasswordResetView
class CustomPasswordResetViewTest(APITestCase):
    """
    Тесты для CustomPasswordResetView.
    """

    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', password='old_password')
        self.url = reverse('password_reset')

    def test_get_method_not_allowed(self):
        """
        Проверяет, что GET запрос к CustomPasswordResetView возвращает 405 Method Not Allowed.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {"detail": "Используйте метод POST для сброса пароля."})

        @patch('users.password_reset_views.PasswordResetForm')
        @patch('users.password_reset_views.CustomPasswordResetView.get_form')
        def test_post_method_success(self, mock_get_form, MockPasswordResetForm):
            """
            Проверяет успешное выполнение POST запроса для сброса пароля.
            Должно быть отправлено письмо и возвращен статус 200 OK.
            """
            mock_form_instance = MagicMock()
            mock_form_instance.is_valid.return_value = True
            mock_form_instance.save.return_value = None

            # Настраиваем mock_get_form так, чтобы он возвращал наш mock_form_instance
            mock_get_form.return_value = mock_form_instance

            data = {'email': 'test@example.com'}
            with self.settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'):
                response = self.client.post(self.url, data, format='json')

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.data, {"detail": "Инструкции по сбросу пароля отправлены на ваш email."})

                # Проверяем, что get_form был вызван
                mock_get_form.assert_called_once()
                mock_form_instance.is_valid.assert_called_once_with()
                # Проверяем, что save() был вызван на экземпляре формы
                mock_form_instance.save.assert_called_once()
                self.assertEqual(len(mail.outbox), 1)
                self.assertEqual(mail.outbox[0].to, ['test@example.com'])

    def test_post_method_invalid_email(self):
        """
        Проверяет, что POST запрос с невалидным email возвращает 400 Bad Request.
        """
        data = {'email': 'invalid-email'}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        self.assertEqual(response.data['email'][0], 'Введите действительный адрес электронной почты.')

    def test_post_method_email_not_found(self):
        """
        Проверяет, что POST запрос с email, который не существует в системе,
        также возвращает 200 OK (для предотвращения перебора email-адресов).
        """
        data = {'email': 'nonexistent@example.com'}
        with self.settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'):
            response = self.client.post(self.url, data, format='json')

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data, {"detail": "Инструкции по сбросу пароля отправлены на ваш email."})
            self.assertEqual(len(mail.outbox), 0)

    def test_post_method_missing_email(self):
        """
        Проверяет, что POST запрос без email возвращает 400 Bad Request.
        """
        data = {}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        self.assertEqual(response.data['email'][0], 'Это поле обязательно.')