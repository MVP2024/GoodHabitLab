from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.views import PasswordResetView
from django.urls import reverse_lazy
from drf_spectacular.utils import (OpenApiExample, OpenApiParameter,
                                   OpenApiResponse, extend_schema)
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from users.models import User
from .serializers import (PasswordResetConfirmSerializer,
                          PasswordResetRequestSerializer)


class APIRootView(generics.GenericAPIView):
    """
        Базовый класс представления API для сброса пароля.
        Определяет сериализатор, используемый в зависимости от URL.
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.request.resolver_match.url_name == "password_reset":
            return PasswordResetRequestSerializer
        elif self.request.resolver_match.url_name == "password_reset_confirm":
            return PasswordResetConfirmSerializer
        return super().get_serializer_class()


@extend_schema(
    summary="Запрос на сброс пароля (отправка email)",
    description="""
    Инициирует процесс сброса пароля, отправляя письмо со ссылкой для восстановления на указанный email.

    Этот эндпоинт используется для начала процедуры восстановления пароля.
    Пользователь должен предоставить свой зарегистрированный email.
    Если email найден, на него будет отправлено письмо со ссылкой для сброса пароля.
    """,
    request=PasswordResetRequestSerializer,
    responses={
        200: OpenApiResponse(
            response={"detail": "Инструкции по сбросу пароля отправлены на ваш email."},
            description="Успешный запрос на сброс пароля.",
            examples=[
                OpenApiExample(
                    "Пример успешного ответа",
                    value={"detail": "Инструкции по сбросу пароля отправлены на ваш email."},
                    response_only=True,
                )
            ]
        ),
        400: OpenApiResponse(
            response={"email": ["Введите действительный адрес электронной почты."]},
            description="Неверный email или его отсутствие.",
            examples=[
                OpenApiExample(
                    "Пример ошибки валидации",
                    value={"email": ["Введите действительный адрес электронной почты."]},
                    response_only=True,
                )
            ]
        ),
    },
    examples=[
        OpenApiExample(
            "Пример запроса",
            value={"email": "user@example.com"},
            request_only=True,
        )
    ],
    tags=["Аутентификация"],
)
class CustomPasswordResetView(APIRootView, PasswordResetView):
    form_class = PasswordResetForm
    success_url = reverse_lazy("password_reset_done")
    email_template_name = "registration/password_reset_email.html"

    # Удалите метод get, чтобы он не возвращал HTML-форму
    def get(self, request, *args, **kwargs):
        return Response(
            {"detail": "Используйте метод POST для сброса пароля."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Создаем экземпляр формы и передаем ей email из валидированных данных сериализатора
        form = self.form_class(data={'email': serializer.validated_data['email']})
        form.is_valid()  # Вызываем is_valid() для заполнения cleaned_data

        form.save(
            request=self.request,
            domain_override=request.META.get("HTTP_HOST"),
            email_template_name=self.email_template_name,
            use_https=request.is_secure(),
        )
        return Response(
            {"detail": "Инструкции по сбросу пароля отправлены на ваш email."},
            status=status.HTTP_200_OK,
        )


@extend_schema(
    summary="Подтверждение сброса пароля (установка нового)",
    description="""
    Подтверждает сброс пароля и устанавливает новый пароль, используя `uidb64` (закодированный ID пользователя)
    и `token` (токен для сброса пароля) из ссылки, полученной на email.

    Этот эндпоинт используется после получения ссылки для сброса пароля на email.
    Параметры `uidb64` и `token` извлекаются из URL, а новый пароль предоставляется в теле запроса.
    """,
    parameters=[
        OpenApiParameter(
            name="uidb64",
            type=str,
            location=OpenApiParameter.PATH,
            description="Закодированный ID пользователя из ссылки для сброса пароля.",
            examples=[
                OpenApiExample(
                    "Пример uidb64",
                    value="MzI",
                )
            ]
        ),
        OpenApiParameter(
            name="token",
            type=str,
            location=OpenApiParameter.PATH,
            description="Токен сброса пароля из ссылки для сброса пароля.",
            examples=[
                OpenApiExample(
                    "Пример токена",
                    value="b8c7r6y-d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6",
                )
            ]
        ),
    ],
    request=PasswordResetConfirmSerializer,
    responses={
        200: OpenApiResponse(
            response={"detail": "Пароль успешно изменен."},
            description="Пароль успешно изменен.",
            examples=[
                OpenApiExample(
                    "Пример успешного ответа",
                    value={"detail": "Пароль успешно изменен."},
                    response_only=True,
                )
            ]
        ),
        400: OpenApiResponse(
            response={"new_password2": ["Пароли не совпадают."]},
            description="Ошибки валидации паролей или неверный токен/uid.",
            examples=[
                OpenApiExample(
                    "Пароли не совпадают",
                    value={"new_password2": ["Пароли не совпадают."]},
                    response_only=True,
                ),
                OpenApiExample(
                    "Неверный UID",
                    value={"uid": ["Неверное значение."]},
                    response_only=True,
                ),
                OpenApiExample(
                    "Недействительный токен",
                    value={"token": ["Недействительный токен."]},
                    response_only=True,
                ),
            ]
        ),
    },
    examples=[
        OpenApiExample(
            "Пример запроса",
            value={
                "new_password1": "new_strong_password",
                "new_password2": "new_strong_password"
            },
            request_only=True,
        )
    ],
    tags=["Аутентификация"],
)
class CustomPasswordResetConfirmView(APIRootView, PasswordResetView):
    """
    Представление для подтверждения сброса пароля и установки нового.
    """
    form_class = PasswordResetForm
    success_url = reverse_lazy("password_reset_complete")

    def get_initial(self):
        return {}

    def get_user(self, uidb64):
        from django.utils.encoding import force_str
        from django.utils.http import urlsafe_base64_decode
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User._default_manager.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        return user

    def post(self, request, *args, **kwargs):
        uidb64 = kwargs.get("uidb64")
        token = kwargs.get("token")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.user = self.get_user(uidb64)
        if not self.user:
            return Response({"uid": ["Неверное значение."]}, status=status.HTTP_400_BAD_REQUEST)

        # Переопределяем self.token_generator, так как он не инициализирован в PasswordResetView
        from django.contrib.auth.tokens import default_token_generator
        self.token_generator = default_token_generator

        if not self.token_generator.check_token(self.user, token):
            return Response({"token": ["Недействительный токен."]}, status=status.HTTP_400_BAD_REQUEST)

        # Используем SetPasswordForm для установки нового пароля
        from django.contrib.auth.forms import SetPasswordForm
        form = SetPasswordForm(user=self.user, data=serializer.validated_data)
        if form.is_valid():
            form.save()
            return Response({"detail": "Пароль успешно изменен."}, status=status.HTTP_200_OK)
        else:
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)
