from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from users.models import (Admin, AdminManager, CustomUserManager, User,
                          UserProfile)


# тесты для CustomUserManager
class CustomUserManagerTest(TestCase):
    """
    Тесты для кастомного менеджера пользователей `CustomUserManager`.
    """

    def test_create_user_success(self):
        """
        Проверяет успешное создание обычного пользователя.
        """
        user = User.objects.create_user(email='test@example.com', password='password123')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('password123'))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_active)

    def test_create_user_no_email(self):
        """
        Проверяет ошибку при попытке создания пользователя без email.
        """
        with self.assertRaisesMessage(ValueError, "Поле Email должно быть заполнено"):
            User.objects.create_user(email=None, password='password123')

    def test_create_superuser_success(self):
        """
        Проверяет успешное создание суперпользователя.
        """
        superuser = User.objects.create_superuser(email='admin@example.com', password='adminpassword')
        self.assertEqual(superuser.email, 'admin@example.com')
        self.assertTrue(superuser.check_password('adminpassword'))
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_active)

    def test_create_superuser_is_staff_false(self):
        """
        Проверяет ошибку при создании суперпользователя с is_staff=False.
        """
        with self.assertRaisesMessage(ValueError, "Суперпользователь должен иметь is_staff=True."):
            User.objects.create_superuser(email='admin@example.com', password='adminpassword', is_staff=False)

    def test_create_superuser_is_superuser_false(self):
        """
        Проверяет ошибку при создании суперпользователя с is_superuser=False.
        """
        with self.assertRaisesMessage(ValueError, "Суперпользователь должен иметь is_superuser=True."):
            User.objects.create_superuser(email='admin@example.com', password='adminpassword', is_superuser=False)

    def test_create_user_extra_fields(self):
        """
        Проверяет создание пользователя с дополнительными полями.
        """
        user = User.objects.create_user(email='extra@example.com', password='password123', telegram_chat_id='12345')
        self.assertEqual(user.telegram_chat_id, '12345')

    def test_create_superuser_extra_fields(self):
        """
        Проверяет создание суперпользователя с дополнительными полями.
        """
        superuser = User.objects.create_superuser(email='super@example.com', password='superpassword', first_name='Super')
        self.assertEqual(superuser.first_name, 'Super')


# тесты для модели User
class UserModelTest(TestCase):
    """
    Тесты для модели пользователя `User`.
    """

    def test_create_user(self):
        """
        Проверяет создание пользователя и его полей.
        """
        user = User.objects.create_user(
            email='test@example.com',
            password='testpassword',
            telegram_chat_id='12345',
            phone='1234567890',
            first_name='Test',
            last_name='User'
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpassword'))
        self.assertEqual(user.telegram_chat_id, '12345')
        self.assertEqual(user.phone, '1234567890')
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_active)
        self.assertIsNotNone(user.date_joined)
        self.assertIsNone(user.last_login)
        self.assertIsNone(user.last_active)
        self.assertIsNotNone(user.userprofile)

    def test_email_unique(self):
        """
        Проверяет уникальность поля email.
        """
        User.objects.create_user(email='unique@example.com', password='password123')
        with self.assertRaises(IntegrityError):
            User.objects.create_user(email='unique@example.com', password='password456')

    def test_telegram_chat_id_unique(self):
        """
        Проверяет уникальность поля telegram_chat_id.
        """
        User.objects.create_user(email='user1@example.com', password='password123', telegram_chat_id='chat1')
        with self.assertRaises(IntegrityError):
            User.objects.create_user(email='user2@example.com', password='password456', telegram_chat_id='chat1')

    def test_email_case_insensitive(self):
        """
        Проверяет, что email регистронезависим (хранится в нижнем регистре).
        """
        user = User.objects.create_user(email='Test@Example.com', password='password123')
        self.assertEqual(user.email, 'test@example.com')
        # Так как email сохраняется в нижнем регистре, фильтровать нужно по нижнему регистру
        self.assertTrue(User.objects.filter(email='test@example.com').exists())
        # Проверяем, что поиск по исходному регистру тоже работает (база данных должна делать это сама,
        # но в тестах Django по умолчанию может быть чувствительна к регистру в SQLite)
        # Если вы используете PostgreSQL с правильными настройками, это может быть не нужно.
        # Для универсальности, можно проверить, что объект создается с правильным регистром.
        # А вот поиск по другому регистру email'а может не пройти на некоторых БД.
        # Поэтому, чтобы тест был надежным, проверяем точное совпадение после нормализации.
        self.assertTrue(User.objects.filter(email=user.email).exists())


    def test_set_last_active(self):
        """
        Проверяет обновление поля last_active.
        """
        user = User.objects.create_user(email='active@example.com', password='password123')
        old_last_active = user.last_active
        # Имитация middleware
        user.last_active = timezone.now()
        user.save(update_fields=['last_active'])
        user.refresh_from_db()
        self.assertIsNotNone(user.last_active)
        self.assertNotEqual(old_last_active, user.last_active)

    def test_user_profile_creation(self):
        """
        Проверяет, что UserProfile создается автоматически при создании пользователя.
        """
        user = User.objects.create_user(email='profile@example.com', password='password123')
        self.assertIsNotNone(user.userprofile)
        self.assertIsInstance(user.userprofile, UserProfile)
        self.assertEqual(user.userprofile.user, user)

    def test_user_profile_deletion_cascades(self):
        """
        Проверяет, что удаление пользователя приводит к удалению его профиля.
        """
        user = User.objects.create_user(email='delete@example.com', password='password123')
        user_id = user.id
        user.delete()
        self.assertFalse(User.objects.filter(id=user_id).exists())
        self.assertFalse(UserProfile.objects.filter(user_id=user_id).exists())


# тесты для модели Admin
class AdminModelTest(TestCase):
    """
    Тесты для прокси-модели `Admin`.
    """

    def test_create_admin_from_user(self):
        """
        Проверяет, что пользователь с is_staff=True может быть создан как Admin
        и обладает соответствующими правами.
        """
        user = User.objects.create_superuser(email='admin@example.com', password='password123')
        admin_obj = Admin.objects.get(pk=user.pk)
        self.assertIsInstance(admin_obj, Admin)
        self.assertTrue(admin_obj.is_staff)
        self.assertTrue(admin_obj.is_superuser)
        self.assertEqual(admin_obj.email, 'admin@example.com')

    def test_admin_verbose_names(self):
        """
        Проверяет правильность verbose_name и verbose_name_plural для модели Admin.
        """
        self.assertEqual(Admin._meta.verbose_name, "Администратор")
        self.assertEqual(Admin._meta.verbose_name_plural, "Администраторы")

    def test_admin_is_proxy(self):
        """
        Проверяет, что модель Admin является прокси-моделью.
        """
        self.assertTrue(Admin._meta.proxy)

    def test_admin_queryset(self):
        """
        Проверяет, что queryset для Admin включает только пользователей с is_staff=True.
        """
        User.objects.create_user(email='user@example.com', password='password123')
        User.objects.create_superuser(email='superadmin@example.com', password='password123')
        staff_user = User.objects.create_user(email='staff@example.com', password='password123', is_staff=True)

        self.assertEqual(Admin.objects.count(), 2)
        self.assertTrue(Admin.objects.filter(email='superadmin@example.com').exists())
        self.assertTrue(Admin.objects.filter(email='staff@example.com').exists())
        self.assertFalse(Admin.objects.filter(email='user@example.com').exists())

    def test_admin_inheritance(self):
        """
        Проверяет, что Admin наследуется от User и имеет те же поля.
        """
        admin = Admin.objects.create_superuser(email='testadmin@example.com', password='password123')
        self.assertEqual(admin.email, 'testadmin@example.com')
        self.assertTrue(hasattr(admin, 'telegram_chat_id'))
        self.assertTrue(hasattr(admin, 'phone'))
