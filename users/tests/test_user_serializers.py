import uuid

from django.db.utils import IntegrityError
from django.test import TestCase
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import User, UserProfile
from users.serializers import (CustomTokenObtainPairSerializer,
                               CustomUserRegistrationSerializer,
                               PasswordResetConfirmSerializer,
                               PasswordResetRequestSerializer,
                               UserProfileSerializer)


# # тесты для CustomTokenObtainPairSerializer
class CustomTokenObtainPairSerializerTest(TestCase):
    """Тесты для CustomTokenObtainPairSerializer."""

    def setUp(self):
        """Создаем тестового пользователя."""
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="testpassword123",
        )
        self.user.telegram_chat_id = "test_chat_id"
        self.user.save()

        self.inactive_user = User.objects.create_user(
            email="inactive@example.com",
            password="testpassword123",
        )
        self.inactive_user.is_active = False
        self.inactive_user.save()


# # тесты для PasswordResetRequestSerializer
class PasswordResetRequestSerializerTest(TestCase):
    """Тесты для PasswordResetRequestSerializer."""

    def test_valid_email(self):
        """Проверяет валидный email."""
        data = {'email': 'test@example.com'}
        serializer = PasswordResetRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['email'], 'test@example.com')

    def test_missing_email(self):
        """Проверяет отсутствие email."""
        data = {}
        serializer = PasswordResetRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
        self.assertEqual(str(serializer.errors['email'][0]), 'Это поле обязательно.')

    def test_invalid_email_format(self):
        """Проверяет неверный формат email."""
        data = {'email': 'invalid-email'}
        serializer = PasswordResetRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
        self.assertEqual(str(serializer.errors['email'][0]), 'Введите действительный адрес электронной почты.')


# # тесты для PasswordResetConfirmSerializer
class PasswordResetConfirmSerializerTest(TestCase):
    """Тесты для PasswordResetConfirmSerializer."""

    def test_valid_passwords(self):
        """Проверяет валидные и совпадающие пароли."""
        data = {
            'new_password1': 'new_strong_password',
            'new_password2': 'new_strong_password'
        }
        serializer = PasswordResetConfirmSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['new_password1'], 'new_strong_password')
        self.assertEqual(serializer.validated_data['new_password2'], 'new_strong_password')

    def test_passwords_do_not_match(self):
        """Проверяет несовпадающие пароли."""
        data = {
            'new_password1': 'password123',
            'new_password2': 'password456'
        }
        serializer = PasswordResetConfirmSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('new_password2', serializer.errors)
        self.assertEqual(str(serializer.errors['new_password2'][0]), 'Пароли не совпадают.')

    def test_missing_new_password1(self):
        """Проверяет отсутствие первого нового пароля."""
        data = {'new_password2': 'new_strong_password'}
        serializer = PasswordResetConfirmSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('new_password1', serializer.errors)
        self.assertEqual(str(serializer.errors['new_password1'][0]), 'Это поле обязательно.')

    def test_missing_new_password2(self):
        """Проверяет отсутствие второго нового пароля."""
        data = {'new_password1': 'new_strong_password'}
        serializer = PasswordResetConfirmSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('new_password2', serializer.errors)
        self.assertEqual(str(serializer.errors['new_password2'][0]), 'Это поле обязательно.')

    def test_empty_password1(self):
        """Проверяет пустой первый новый пароль."""
        data = {
            'new_password1': '',
            'new_password2': 'new_strong_password'
        }
        serializer = PasswordResetConfirmSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('new_password1', serializer.errors)
        self.assertEqual(str(serializer.errors['new_password1'][0]), 'Это поле обязательно.')

    def test_empty_password2(self):
        """Проверяет пустой второй новый пароль."""
        data = {
            'new_password1': 'new_strong_password',
            'new_password2': ''
        }
        serializer = PasswordResetConfirmSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('new_password2', serializer.errors)
        self.assertEqual(str(serializer.errors['new_password2'][0]), 'Это поле обязательно.')

    def test_passwords_match_but_empty(self):
        """Проверяет совпадающие, но пустые пароли."""
        data = {
            'new_password1': '',
            'new_password2': ''
        }
        serializer = PasswordResetConfirmSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('new_password1', serializer.errors)
        self.assertIn('new_password2', serializer.errors)
        self.assertEqual(str(serializer.errors['new_password1'][0]), 'Это поле обязательно.')
        self.assertEqual(str(serializer.errors['new_password2'][0]), 'Это поле обязательно.')


class UserProfileSerializerTest(TestCase):
    """Тесты для UserProfileSerializer."""

    def setUp(self):
        """Создание тестового пользователя и профиля."""
        # Создаем пользователя, UserProfile будет создан автоматически сигналом post_save
        self.user = User.objects.create_user(email=f"test_{uuid.uuid4()}@example.com", password="password123")
        # Получаем UserProfile, который был создан автоматически
        self.user_profile = self.user.userprofile
        # Обновляем поля для теста, если необходимо
        self.user_profile.bio = "Тестовая биография."
        self.user_profile.notify_email = True
        self.user_profile.notify_telegram = False
        self.user_profile.reminder_frequency = "daily"
        self.user_profile.reminder_time = "10:00:00"
        self.user_profile.streak = 5
        self.user_profile.rewards_count = 2
        self.user_profile.save()

        self.serializer = UserProfileSerializer(instance=self.user_profile)

    def test_contains_expected_fields(self):
        """Проверяет, что сериализатор содержит все ожидаемые поля."""
        data = self.serializer.data
        expected_fields = {
            "bio", "notify_email", "notify_telegram",
            "reminder_frequency", "reminder_time", "streak", "rewards_count", "user"
        }
        self.assertSetEqual(set(data.keys()), expected_fields)


    def test_field_content(self):
        """Проверяет содержимое полей."""
        data = self.serializer.data
        self.assertEqual(data["bio"], self.user_profile.bio)
        self.assertEqual(data["notify_email"], self.user_profile.notify_email)
        self.assertEqual(data["notify_telegram"], self.user_profile.notify_telegram)
        self.assertEqual(data["reminder_frequency"], self.user_profile.reminder_frequency)
        self.assertEqual(data["reminder_time"], str(self.user_profile.reminder_time))
        self.assertEqual(data["streak"], self.user_profile.streak)
        self.assertEqual(data["rewards_count"], self.user_profile.rewards_count)

    def test_update_profile(self):
        """Проверяет обновление существующего профиля пользователя."""
        updated_data = {
            "bio": "Обновленная биография.",
            "notify_telegram": True,
            "reminder_frequency": "weekly"
        }
        serializer = UserProfileSerializer(instance=self.user_profile, data=updated_data, partial=True)
        self.assertTrue(serializer.is_valid(raise_exception=True))
        updated_profile = serializer.save()

        self.user_profile.refresh_from_db()
        self.assertEqual(self.user_profile.bio, updated_data["bio"])
        self.assertTrue(self.user_profile.notify_telegram)
        self.assertEqual(self.user_profile.reminder_frequency, updated_data["reminder_frequency"])


    def test_invalid_reminder_frequency(self):
        """Проверяет валидацию с некорректной частотой напоминаний."""
        invalid_data = {"reminder_frequency": "yearly"}
        serializer = UserProfileSerializer(instance=self.user_profile, data=invalid_data, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn("reminder_frequency", serializer.errors)
        self.assertIn('Значения yearly нет среди допустимых вариантов.', str(serializer.errors["reminder_frequency"][0]))


class CustomUserRegistrationSerializerTest(TestCase):
    """Тесты для CustomUserRegistrationSerializer."""

    def setUp(self):
        self.user_data = {
            "email": f"new_user_{uuid.uuid4()}@example.com",
            "password": "strong_password",
            "telegram_chat_id": f"new_chat_id_{uuid.uuid4().hex[:10]}"
        }
        self.existing_user = User.objects.create_user(
            email=f"existing_{uuid.uuid4()}@example.com",
            password="existing_password",
            telegram_chat_id=f"existing_chat_id_{uuid.uuid4().hex[:10]}"
        )

    def test_registration_with_existing_email(self):
        """Проверяет, что регистрация с существующим email отклоняется."""
        invalid_data = self.user_data.copy()
        invalid_data["email"] = self.existing_user.email  # Используем существующий email
        # Убедимся, что telegram_chat_id также уникален для этого теста
        invalid_data["telegram_chat_id"] = f"unique_chat_for_invalid_email_{uuid.uuid4().hex[:10]}"

        serializer = CustomUserRegistrationSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)
        # Проверяем, что сообщение об ошибке соответствует ожидаемому
        self.assertEqual(
            str(serializer.errors["email"][0]),
            'пользователь с таким Email уже существует.'
        )

    def test_registration_with_existing_telegram_chat_id(self):
        """Проверяет, что регистрация с существующим telegram_chat_id отклоняется."""
        invalid_data = self.user_data.copy()
        invalid_data["telegram_chat_id"] = self.existing_user.telegram_chat_id
        # Убедимся, что email также уникален для этого теста
        invalid_data["email"] = f"unique_email_for_invalid_chat_id_{uuid.uuid4()}@example.com"

        serializer = CustomUserRegistrationSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("telegram_chat_id", serializer.errors)
        # Проверяем, что сообщение об ошибке соответствует ожидаемому
        self.assertEqual(
            str(serializer.errors["telegram_chat_id"][0]),
            'пользователь с таким Telegram Chat ID уже существует.'
        )

    def test_registration_with_missing_email(self):
        """Проверяет, что email является обязательным полем."""
        invalid_data = self.user_data.copy()
        del invalid_data["email"]
        serializer = CustomUserRegistrationSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)
        self.assertEqual(str(serializer.errors["email"][0]), 'Обязательное поле.')

    def test_registration_with_missing_password(self):
        """Проверяет, что password является обязательным полем."""
        invalid_data = self.user_data.copy()
        del invalid_data["password"]
        serializer = CustomUserRegistrationSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)
        self.assertEqual(str(serializer.errors["password"][0]), 'Обязательное поле.')

    def test_create_user_method(self):
        """Проверяет корректность вызова create_user в методе create сериализатора."""
        # Для уникальности email и telegram_chat_id в этом тесте
        unique_email = f"test_create_method_{uuid.uuid4()}@example.com"
        unique_chat_id = f"create_method_chat_{uuid.uuid4().hex[:10]}"
        user_data_for_create_method = {
            "email": unique_email,
            "password": "password123",
            "telegram_chat_id": unique_chat_id
        }

        serializer = CustomUserRegistrationSerializer(data=user_data_for_create_method)
        self.assertTrue(serializer.is_valid())
        user = serializer.create(serializer.validated_data)
        self.assertEqual(user.email, user_data_for_create_method["email"])
        self.assertTrue(user.check_password(user_data_for_create_method["password"]))
        self.assertEqual(user.telegram_chat_id, user_data_for_create_method["telegram_chat_id"])
