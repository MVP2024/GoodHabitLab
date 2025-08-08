import logging

from django.contrib.auth.models import AnonymousUser
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, mixins, serializers, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import (TokenObtainPairView,
                                            TokenRefreshView)

from .models import User
from .serializers import (CustomTokenObtainPairSerializer,
                          CustomUserRegistrationSerializer,
                          UserProfileUpdateSerializer, UserSerializer)

logger = logging.getLogger(__name__)


@extend_schema_view(
    post=extend_schema(
        summary="Получение JWT-токена (авторизация)",
        description="""
        Получить access и refresh JWT-токены.

        Передайте email и пароль в теле запроса.

        Пример запроса:
        ```json
        {
          "email": "user@example.com",
          "password": "password123"
        }
        ```
        Пример ответа (201):
        ```json
        {
          "refresh": "<refresh>",
          "access": "<access>",
          "id": 1,
          "email": "user@example.com",
          "telegram_chat_id": "12345678"
        }
        ```

        Ошибка авторизации пример (401):
        ```json
        {"detail": "No active account found with the given credentials"}
        ```
        """,
        tags=["api"],
    )
)
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


@extend_schema(
    summary="Регистрация нового пользователя (только email)",
    description="Регистрирует нового пользователя только с email, паролем и (опционально) telegram_chat_id. "
    "Проверяет уникальность email и telegram_chat_id.",
    tags=["Пользователи"],
    request=CustomUserRegistrationSerializer,
    responses={201: CustomUserRegistrationSerializer},
)
class UserRegistrationAPIView(generics.CreateAPIView):
    serializer_class = CustomUserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs) -> Response:
        logger.info(f"Попытка регистрации пользователя с email: {request.data.get('email')}")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        logger.info(f"Пользователь успешно зарегистрирован: {serializer.data.get('email')}")
        return Response(
            {"message": "Пользователь успешно зарегистрирован."},
            status=status.HTTP_201_CREATED,
            headers=headers,
        )


@extend_schema(
    summary="Работа с профилем пользователя",
    description="Позволяет просматривать и изменять (только своё) поле telegram_chat_id текущего пользователя. "
    "Доступно только для аутентифицированных пользователей.",
    tags=["Пользователи"],
)
class UserProfileViewSet(viewsets.ReadOnlyModelViewSet, mixins.UpdateModelMixin):
    """
    ViewSet для просмотра и обновления профиля текущего пользователя.
    Позволяет пользователю просматривать свои данные и обновлять telegram_chat_id.
    """

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_object(self) -> User | AnonymousUser:
        """
        Возвращает объект пользователя, связанный с текущим запросом.
        Для действия 'retrieve' возвращает текущего пользователя.
        Для других действий (например, update/partial_update),
        если они будут использоваться с конкретным pk, будет использоваться стандартное поведение.
        """
        if self.action == 'retrieve':
            return self.request.user
        return super().get_object()

    def get_queryset(self):
        """
        Переопределяем get_queryset, чтобы он всегда возвращал только текущего пользователя.
        """
        return User.objects.filter(pk=self.request.user.pk).order_by('id')

    def get_serializer_class(self):
        """
        Возвращает соответствующий класс сериализатора в зависимости от действия.
        Для обновления используется UserProfileUpdateSerializer, для других действий - UserSerializer.
        """
        if self.action == "partial_update":
            return UserProfileUpdateSerializer
        return UserSerializer

    @extend_schema(
        summary="Список профилей (только вашего профиля)",
        description="Возвращает только ваш собственный профиль пользователя. Для совместимости со стандартным "
        "роутером, list-метод, хотя возвращает один объект в списке.",
        tags=["Пользователи"],
        responses=UserSerializer(many=True),
    )
    def list(self, request, *args, **kwargs):
        # Поскольку get_queryset возвращает только текущего пользователя,
        # этот list метод будет возвращать список с одним элементом.
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Посмотреть ваш профиль пользователя",
        description="Получить подробную информацию о себе — email, telegram_chat_id.",
        tags=["Пользователи"],
        responses=UserSerializer,
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Полностью обновить профиль пользователя",
        description="Полностью заменить данные профиля пользователя. Поддерживается только изменение telegram_chat_id, "
        "остальные поля доступны только для чтения.",
        tags=["Пользователи"],
        request=UserProfileUpdateSerializer,
        responses=UserSerializer,
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary="Частично обновить профиль пользователя",
        description="Обновить одно или несколько полей (например, telegram_chat_id) вашего профиля.",
        tags=["Пользователи"],
        request=UserProfileUpdateSerializer,
        responses=UserSerializer,
    )
    def partial_update(self, request, *args, **kwargs) -> Response:
        """
        Частичное обновление профиля пользователя, например, telegram_chat_id.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


@extend_schema_view(
    post=extend_schema(
        summary="Обновление access-токена по refresh-токену",
        description="""
        Получить новый access-токен, используя refresh-токен.

        Пример запроса:
        ```json
        { "refresh": "<refresh>" }
        ```
        Пример ответа (200):
        ```json
        { "access": "<access>" }
        ```

        Ошибка refresh-токена пример (401):
        ```json
        {"detail": "Token is invalid or expired"}
        ```
        """,
        tags=["api"],
    )
)
class CustomTokenRefreshView(TokenRefreshView):
    """
    Получение нового access-токена по refresh-токену.
    """
    authentication_classes = []
