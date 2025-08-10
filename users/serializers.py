import logging

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User, UserProfile

logger = logging.getLogger(__name__)


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели пользователя.
    Используется для вывода и обновления данных пользователя, включая telegram_chat_id.
    """

    class Meta:
        model = User
        fields = ("id", "email", "telegram_chat_id")
        read_only_fields = (
            "id",
            "email",
        )  # Пользователь не может менять email через этот сериализатор


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для обновления профиля пользователя.
    Позволяет пользователю обновить свой telegram_chat_id.
    """
    class Meta:
        model = User
        fields = ("telegram_chat_id",)

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        return instance


class CustomUserRegistrationSerializer(serializers.ModelSerializer):
    """
        Сериализатор для регистрации нового пользователя через API.
        Позволяет регистрировать пользователя с email, паролем и опциональным telegram_chat_id,
        обеспечивая уникальность email и telegram_chat_id.
    """

    class Meta:
        model = User
        fields = ("email", "password", "telegram_chat_id")
        extra_kwargs = {
            "password": {"write_only": True},
        }

    def validate(self, attrs):
        email = attrs.get("email")
        telegram_chat_id = attrs.get("telegram_chat_id")

        errs = {}

        if email and User.objects.filter(email=email).exists():
            errs["email"] = "Пользователь с таким email уже существует. Войдите или восстановите пароль."
        if telegram_chat_id and User.objects.filter(telegram_chat_id=telegram_chat_id).exists():
            errs["telegram_chat_id"] = ("Этот Telegram Chat ID уже привязан к другому аккаунту. "
                                        "Войдите или используйте другой.")
        if errs:
            logger.warning(
                f"Проблема регистрации (email: {email}, telegram_chat_id: {telegram_chat_id}): {errs}")
            raise serializers.ValidationError(errs)
        return attrs

    def create(self, validated_data):
        """
        Создает и возвращает нового пользователя, используя менеджер create_user
        для правильной обработки пароля.
        """
        email = validated_data["email"]
        password = validated_data["password"]
        telegram_chat_id = validated_data.get("telegram_chat_id")

        user = User.objects.create_user(
            email=email,
            password=password,
            telegram_chat_id=telegram_chat_id,
        )
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """
        Сериализатор для модели UserProfile.
        Используется для вывода и обновления данных профиля пользователя,
        таких как био, настройки уведомлений и другая информация.
    """
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = UserProfile
        fields = (
            "bio",
            "notify_email",
            "notify_telegram",
            "reminder_frequency",
            "reminder_time",
            "streak",
            "rewards_count",
            "user",
        )


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, error_messages={
        'required': 'Это поле обязательно.',
        'invalid': 'Введите действительный адрес электронной почты.',
    })


class PasswordResetConfirmSerializer(serializers.Serializer):
    new_password1 = serializers.CharField(required=True, error_messages={'required': 'Это поле обязательно.',
                                                                         'blank': 'Это поле обязательно.'})
    new_password2 = serializers.CharField(required=True, error_messages={'required': 'Это поле обязательно.',
                                                                         'blank': 'Это поле обязательно.'})

    def validate(self, data):
        if data['new_password1'] != data['new_password2']:
            raise serializers.ValidationError({"new_password2": "Пароли не совпадают."})
        return data


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = "email"

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")  # Получаем пароль

        if not email:
            raise serializers.ValidationError({"email": "Это поле обязательно."})
        if not password:
            raise serializers.ValidationError({"password": "Это поле обязательно."})

        logger.info(f"Попытка входа с email: {email}")
        try:
            data = super().validate(attrs)
        except serializers.ValidationError as e:
            # Перехватываем стандартное сообщение от simplejwt и заменяем его
            if "No active account found with the given credentials" in str(e):
                raise serializers.ValidationError(
                    {"detail": "Не найдено активной учетной записи с указанными учетными данными."})
            raise e

        if not self.user.is_active:
            logger.warning(f"Неактивный пользователь попытался войти: {email}")
            raise serializers.ValidationError("Аккаунт не активен.")
        data.update(
            {
                "id": self.user.id,
                "email": self.user.email,
                "telegram_chat_id": getattr(self.user, "telegram_chat_id", None),
            }
        )
        logger.info(f"Успешный вход пользователя: {self.user.email}")
        return data
