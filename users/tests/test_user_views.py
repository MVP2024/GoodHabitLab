from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import User


# тесты для CustomTokenObtainPairView
class CustomTokenObtainPairViewTest(APITestCase):
    def setUp(self):
        """
        Создаем тестового пользователя и url для эндпоинта авторизации.

        """
        self.url = reverse('token_obtain_pair')
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123'
        )

    def test_login_success(self):
        """Успешная авторизация возвращает токены и данные пользователя"""
        response = self.client.post(self.url, {
            'email': 'testuser@example.com',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['email'], 'testuser@example.com')
        self.assertEqual(response.data['id'], self.user.id)

    def test_login_wrong_password(self):
        """Неверный пароль возвращает ошибку 401"""
        response = self.client.post(self.url, {
            'email': 'testuser@example.com',
            'password': "wrongpass"
        })
        self.assertEqual(response.status_code, 401)
        self.assertIn('detail', response.data)

    def test_login_user_not_found(self):
        """Несуществующий пользователь возвращает ошибку 401"""
        response = self.client.post(self.url, {
            'email': 'unknown@example.com',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 401)


# тесты для UserRegistrationAPIView
class UserRegistrationAPIViewTest(APITestCase):
    def setUp(self):
        self.url = reverse('register')
        self.valid_data = {
            'email': 'newuser@example.com',
            'password': 'testpass123',
            'telegram_chat_id': '12345678'
        }

    def test_registration_success(self):
        """Успешная регистрация возвращает 201 и сообщение"""
        response = self.client.post(self.url, self.valid_data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['message'], 'Пользователь успешно зарегистрирован.')
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())

    def test_registration_email_unique(self):
        """Повторная регистрация с тем же email возвращает ошибку"""
        self.client.post(self.url, self.valid_data)
        response = self.client.post(self.url, self.valid_data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('email', response.data)

    def test_registration_telegram_chat_id_unique(self):
        """Регистрация с существующим telegram_chat_id возвращает ошибку"""
        self.client.post(self.url, self.valid_data)
        response = self.client.post(self.url, {
            **self.valid_data,
            'email': 'another@example.com'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('telegram_chat_id', response.data)

    def test_registration_password_required(self):
        """Пароль обязателен"""
        data = {'email': 'newuser@example.com'}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('password', response.data)

    def test_registration_email_required(self):
        """Email обязателен"""
        data = {'password': 'testpass123'}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('email', response.data)


# тесты для UserProfileViewSet
class UserProfileViewSetTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse('user-profile-detail', kwargs={'pk': self.user.pk})

    def test_retrieve_profile_success(self):
        """Просмотр профиля возвращает 200 и данные пользователя"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.data['email'], self.user.email)
        self.assertEqual(response.data['id'], self.user.id)

    def test_update_telegram_chat_id_success(self):
        """Успешное обновление telegram_chat_id возвращает 200"""
        response = self.client.patch(reverse('user-profile-detail', kwargs={'pk': self.user.pk}), {'telegram_chat_id': '87654321'})
        self.assertEqual(response.status_code, 200) # Ожидаем 200 OK при успешном обновлении
        self.user.refresh_from_db()
        self.assertEqual(self.user.telegram_chat_id, '87654321')

    def test_update_forbidden_fields_ignored(self):
        """Попытка обновить запрещённые поля (email) игнорируется"""
        response = self.client.patch(reverse('user-profile-detail', kwargs={'pk': self.user.pk}), {'email': 'hacked@example.com'})
        self.assertEqual(response.status_code, 200) # Ожидаем 200 OK при успешном обновлении (игнорирование поля)
        self.user.refresh_from_db()
        self.assertNotEqual(self.user.email, 'hacked@example.com')

    def test_unauthenticated_access_denied(self):
        """Неаутентифицированный доступ запрещён"""
        self.client.logout()
        response = self.client.get(reverse('user-profile-detail', kwargs={'pk': self.user.pk}))
        self.assertEqual(response.status_code, 401)


class CustomTokenRefreshViewTest(APITestCase):
    def setUp(self):
        self.url = reverse('token_refresh')
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123'
        )
        # Получаем refresh-токен для тестового пользователя
        refresh = RefreshToken.for_user(self.user)
        self.refresh_token = str(refresh)
        self.invalid_refresh_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTY3ODAwMDc5NiwianRpIjoiZmVkY2JhOTAtZWYxNC00OWM1LWIwZWMtNGU4ZjhkNzE3MGRlIiwidXNlcl9pZCI6MX0.invalid'

    def test_token_refresh_success(self):
        """Успешное обновление access-токена с использованием refresh-токена"""
        response = self.client.post(self.url, {'refresh': self.refresh_token})
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_token_refresh_invalid_token(self):
        """Попытка обновления с невалидным refresh-токеном"""
        response = self.client.post(self.url, {'refresh': self.invalid_refresh_token})
        self.assertEqual(response.status_code, 401)
        self.assertIn('detail', response.data)
        self.assertEqual(response.data['detail'], 'Token is invalid')

    def test_token_refresh_no_token_provided(self):
        """Попытка обновления без предоставления refresh-токена"""
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 400)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['refresh'][0], 'Обязательное поле.')
