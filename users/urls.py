from django.urls import path, re_path
from rest_framework.routers import DefaultRouter

from .password_reset_views import (CustomPasswordResetConfirmView,
                                   CustomPasswordResetView)
from .views import (CustomTokenObtainPairView, CustomTokenRefreshView,
                    UserProfileViewSet, UserRegistrationAPIView)

router = DefaultRouter()
router.register(r"profile", UserProfileViewSet, basename="user-profile")

urlpatterns = [
    path("register/", UserRegistrationAPIView.as_view(), name="register"),
    path(
        "token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"
    ),  # Авторизация
    path(
        "token/refresh/", CustomTokenRefreshView.as_view(), name="token_refresh"
    ),  # Обновление токена
    path(
        "password_reset/",
        CustomPasswordResetView.as_view(),
        name="password_reset",
    ),
    re_path(
        r"password_reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,32})/",
        CustomPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
]

urlpatterns += router.urls
