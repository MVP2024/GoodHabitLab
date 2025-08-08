import os
from datetime import timedelta
from pathlib import Path

from celery.schedules import \
    crontab  # Используем crontab для более гибкого расписания
from dotenv import load_dotenv

load_dotenv()  # Загружаем переменные окружения из .env

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY")

DEBUG = os.getenv("DEBUG", "False").lower() == "true"

ALLOWED_HOSTS_ENV = os.getenv("ALLOWED_HOSTS", "")
if not DEBUG:
    ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS_ENV.split(",") if host.strip()]
    if not ALLOWED_HOSTS:
        raise ValueError("Для DEBUG=False необходимо задать ALLOWED_HOSTS в .env")
    ALLOWED_HOSTS.extend([".ngrok-free.app", "127.0.0.1", "localhost"])  # Добавил эту строчку
else:
    ALLOWED_HOSTS = ["*"]

BASE_URL = os.getenv("BASE_URL",
                     "http://127.0.0.1:8000")

AUTH_USER_MODEL = "users.User"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "rest_framework",
    "drf_spectacular",  # Для документации
    "corsheaders",  # Для CORS
    "habits",  # Твое новое приложение
    "django_celery_beat",  # Для Celery Beat
    "telegram_bot",  # Новое приложение для Telegram
    "django_filters",  # Для фильтрации в API
    "users",
]

MIDDLEWARE = [
    'users.middleware.LastActiveMiddleware',
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "config/templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": os.getenv(
            "DB_NAME",
        ),
        "USER": os.getenv(
            "DB_USER",
        ),
        "PASSWORD": os.getenv(
            "DB_PASSWORD",
        ),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "ru-ru"

TIME_ZONE = "Europe/Moscow"  # Устанавливаем часовой пояс

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# REST Framework settings
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 5,
}

# DRF Spectacular settings (API Documentation)
SPECTACULAR_SETTINGS = {
    "TITLE": "Good Habit Lab API",
    "DESCRIPTION": "API для управления привычками и пользователями",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SECURITY": [
        {
            "BearerAuth": [],
        }
    ],
    "COMPONENTS": {
        "securitySchemes": {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "**Введите ваш JWT токен без 'Bearer ' префикса.** Пример: `eyJ0eXAiOiJKV1Qi...`"
            }
        }
    },
    "EXCLUDE_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
}

# Настройки CORS
CORS_ORIGIN_ALLOW_ALL = True  # В режиме разработки разрешаем все источники

# Celery settings
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE  # Должен совпадать с TIME_ZONE Django
CELERY_IMPORTS = (
    'habits.tasks',
    'telegram_bot.tasks',
)

# Настройка JWT
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=360),  # Время жизни access токена
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),  # Время жизни refresh токена
    "ROTATE_REFRESH_TOKENS": True,  # Ротация refresh токенов
    "BLACKLIST_AFTER_ROTATION": True,  # Занесение в черный список после ротации
    "UPDATE_LAST_LOGIN": False,  # Обновлять поле last_login при использовании токена
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": None,
    "AUDIENCE": None,
    "ISSUER": None,
    "JWK_URL": None,
    "LEEWAY": 0,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",
    "JTI_CLAIM": "jti",
    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(minutes=5),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1),
}

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/"  # Определяем базовый URL для Telegram API

CELERY_BEAT_SCHEDULE = {
    "check-and-send-daily-habit-reminders-every-minute": {
        "task": "habits.tasks.check_and_send_daily_habit_reminders",
        "schedule": crontab(
            minute="*"
        ),  # Запускать каждые 60 секунд (или другое удобное время)
        "args": (),
    },
    'send-inactive-user-reminders': {
        'task': 'telegram_bot.tasks.poll_inactive_users',
        'schedule': crontab(hour=10, minute=0),
    },
}

# Настройки Email
# EMAIL_BACKEND по умолчанию устанавливается в console.EmailBackend для разработки.
# Для использования реальной отправки через SMTP, установите EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend'
# в вашем .env файле.
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = os.getenv("EMAIL_PORT")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "False").lower() == "true"
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "False").lower() == "true"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
DEFAULT_FROM_EMAIL = os.getenv("EMAIL_HOST_USER", "webmaster@localhost")
