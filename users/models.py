from typing import Any

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class CustomUserManager(BaseUserManager):
    """
    Пользовательский менеджер модели User, который использует email в качестве уникального идентификатора
    для аутентификации вместо username.
    """

    def create_user(self, email, password=None, **extra_fields):
        """
        Создает и сохраняет обычного пользователя с заданным email и паролем.
        """
        if not email:
            raise ValueError("Поле Email должно быть заполнено")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Создает и сохраняет суперпользователя с заданным email и паролем.
        Суперпользователь автоматически получает права is_staff=True, is_superuser=True и is_active=True.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Суперпользователь должен иметь is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Суперпользователь должен иметь is_superuser=True.")
        return self.create_user(email, password, **extra_fields)


class AdminManager(CustomUserManager):
    def get_queryset(self, *args: Any, **kwargs: Any) -> models.QuerySet[Any]:
        return super().get_queryset(*args, **kwargs).filter(is_staff=True)


class User(AbstractUser):
    telegram_chat_id = models.CharField(
        max_length=100, blank=True, null=True, unique=True, verbose_name="Telegram Chat ID", help_text="Укажите свой Telegram Chat ID"
    )
    email = models.EmailField(
        unique=True, blank=False, null=False, verbose_name="Email", help_text="Укажите свой Email"
    )
    last_active = models.DateTimeField(null=True, blank=True, verbose_name='Последняя активность',
                                       help_text="Дата и время последней активности пользователя")
    username = None  # Устанавливаем username в None
    phone = models.CharField(
        max_length=35,
        blank=True,
        null=True,
        verbose_name="Телефон",
        help_text="Укажите свой телефон",
    )
    avatar = models.ImageField(
        upload_to="users/avatars_users/",
        blank=True,
        null=True,
        verbose_name="Аватар",
        help_text="Загрузите свой аватар",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()


class Admin(User):
    objects = AdminManager()

    class Meta:
        proxy = True
        verbose_name = "Администратор"
        verbose_name_plural = "Администраторы"


class UserProfile(models.Model):
    REMINDER_CHOICES = [
        ("never", "Никогда"),
        ("daily", "Ежедневно"),
        ("weekly", "Раз в неделю"),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    notify_email = models.BooleanField(default=True)
    notify_telegram = models.BooleanField(default=True)
    streak = models.PositiveIntegerField(default=0, verbose_name="Текущий стрик",
                                         help_text="Количество дней подряд, когда пользователь выполнял задачи")
    rewards_count = models.PositiveIntegerField(default=0)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reminder_frequency = models.CharField(max_length=10, choices=REMINDER_CHOICES, default='never',
                                          verbose_name="Частота напоминаний", help_text="Выберите частоту напоминаний")
    reminder_time = models.TimeField(blank=True, null=True, verbose_name="Время напоминания",
                                     help_text="Укажите время напоминания")

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"


@receiver(post_save, sender=User)
def create_or_update_user_profile(_sender: type[User], instance: User, created: bool, **_kwargs: dict) -> None:
    if created:
        UserProfile.objects.create(user=instance)
    instance.userprofile.save()
