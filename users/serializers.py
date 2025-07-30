from rest_framework import serializers
import logging

from .models import User, UserProfile


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели пользователя.
    Используется для вывода и обновления данных пользователя, включая telegram_chat_id.
    """
    nickname = serializers.CharField(source='userprofile.nickname', read_only=True)

    class Meta:
        model = User
        fields = ("id", "email", "telegram_chat_id", "nickname")
        read_only_fields = (
            "id",
            "email",
        )  # Пользователь не может менять email через этот сериализатор


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для обновления профиля пользователя.
    Позволяет пользователю обновить свой telegram_chat_id и nickname.
    """
    nickname = serializers.CharField(source='userprofile.nickname', required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ("telegram_chat_id", "nickname")

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('userprofile', {})
        nickname = profile_data.get('nickname')

        instance = super().update(instance, validated_data)

        # Обновляем или создаем UserProfile, если есть nickname
        if nickname is not None:
            user_profile, _ = UserProfile.objects.get_or_create(user=instance)
            user_profile.nickname = nickname
            user_profile.save()
        return instance


class CustomUserRegistrationSerializer(serializers.ModelSerializer):
    """
        Сериализатор для регистрации нового пользователя через API.
        Позволяет регистрировать пользователя с email, паролем и опциональным telegram_chat_id,
        обеспечивая уникальность email и telegram_chat_id.
    """
    nickname = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ("email", "password", "telegram_chat_id", "nickname")
        extra_kwargs = {
            "password": {"write_only": True},
        }

    def validate(self, attrs):
        email = attrs.get("email")
        telegram_chat_id = attrs.get("telegram_chat_id")
        errs = {}
        if User.objects.filter(email=email).exists():
            errs["email"] = "Пользователь с таким email уже существует. Войдите или восстановите пароль."
        if telegram_chat_id and User.objects.filter(telegram_chat_id=telegram_chat_id).exists():
            errs[
                "telegram_chat_id"] = ("Этот Telegram Chat ID уже привязан к другому аккаунту. "
                                       "Войдите или используйте другой.")
        if errs:
            logger = logging.getLogger(__name__)
            logger.warning(f"Проблема регистрации (email: {email}, telegram_chat_id: {telegram_chat_id}): {errs}")
            raise serializers.ValidationError(errs)
        return attrs

    def create(self, validated_data):
        email = validated_data.get("email")
        password = validated_data.get("password")
        telegram_chat_id = validated_data.get("telegram_chat_id", None)
        nickname = validated_data.pop("nickname", None) # Извлекаем nickname

        user = User.objects.create_user(email=email, telegram_chat_id=telegram_chat_id)
        user.set_password(password)
        user.save()

        if nickname:
            UserProfile.objects.create(user=user, nickname=nickname)

        logger = logging.getLogger(__name__)
        logger.info(f"Новый пользователь зарегистрирован: {email}")
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """
        Сериализатор для модели UserProfile.
        Используется для вывода и обновления данных профиля пользователя,
        таких как аватар, био, настройки уведомлений, никнейм и другая информация.
    """
    nickname = serializers.CharField(source='nickname', required=False, allow_blank=True)

    class Meta:
        model = UserProfile
        fields = (
            "avatar",
            "bio",
            "notify_email",
            "notify_telegram",
            "reminder_frequency",
            "reminder_time",
            "streak",
            "rewards_count",
            "nickname"
        )


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    new_password1 = serializers.CharField(required=True)
    new_password2 = serializers.CharField(required=True)

    def validate(self, data):
        if data['new_password1'] != data['new_password2']:
            raise serializers.ValidationError({"new_password2": "Пароли не совпадают."})
        return data
