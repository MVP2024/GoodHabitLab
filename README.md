# GoodHabitLab

GoodHabitLab — это веб-приложение и Telegram-бот, разработанный для помощи пользователям в формировании и отслеживании
полезных привычек. Проект включает в себя REST API для управления привычками, категории привычек, систему логов
выполнения и уведомлений, а также интеграцию с Telegram для напоминаний и интерактивного взаимодействия.

## Описание проекта

Проект разработан с использованием Django REST Framework для бэкенда и PostgreSQL в качестве базы данных. Для
асинхронной обработки задач и планирования напоминаний используются Celery и Redis. Интеграция с Telegram реализована
через вебхуки и Telegram Bot API, что позволяет пользователям получать напоминания и управлять привычками
непосредственно из мессенджера.

**Ключевые особенности:**

* **Управление привычками:** Создание, редактирование, удаление, просмотр личных и публичных привычек.
* **Категории привычек:** Классификация привычек для удобства организации и анализа.
* **Логи выполнения:** Отслеживание прогресса выполнения привычек с возможностью пометки выполнения и откладывания.
* **Уведомления Telegram:** Ежедневные напоминания и интерактивные кнопки для действий с привычками через Telegram-бот.
* **Система вознаграждений:** Возможность устанавливать вознаграждения за выполнение привычек.
* **Гибкая периодичность:** Поддержка ежедневных, еженедельных, ежемесячных и пользовательских расписаний для привычек.
* **Аутентификация JWT:** Безопасная аутентификация пользователей с помощью JWT-токенов.
* **Интерактивная документация API:** Используется `drf-spectacular` для генерации Swagger/OpenAPI документации.

## Технологии

* **Backend:** Python, Django REST Framework
* **База данных:** PostgreSQL
* **Очередь сообщений/Брокер:** Redis
* **Асинхронные задачи:** Celery, `django-celery-beat`
* **Telegram Bot API:** Интеграция через вебхуки
* **Аутентификация:** `djangorestframework-simplejwt`
* **Документация API:** `drf-spectacular`
* **Загрузка данных:** `python-dotenv`

## Запуск проекта

Для успешного запуска проекта вам потребуются:

* **Python 3.10+**
* **Poetry** (рекомендуется для управления зависимостями)
* **Docker Desktop** (для запуска PostgreSQL и Redis) или установленные PostgreSQL и Redis напрямую.
* **ngrok** (для туннелирования локального сервера Telegram вебхукам)

### 1. Клонирование репозитория и установка зависимостей

```
git clone <URL вашего репозитория>
cd GoodHabitLab
poetry install
```

### 2. Настройка переменных окружения

Создайте файл .env в корне проекта на основе .env.example и заполните его:

```
# .env

SECRET_KEY=your_django_secret_key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# Database settings (PostgreSQL)
DB_NAME=goodhabitlab_db
DB_USER=goodhabitlab_user
DB_PASSWORD=goodhabitlab_password
DB_HOST=localhost
DB_PORT=5432

# Redis for Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Telegram Bot API
TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID=YOUR_TELEGRAM_CHAT_ID # (опционально, для тестовых отправок)
BASE_URL=http://your_ngrok_url # Пример: https://abcdef123456.ngrok-free.app

# Email settings (для сброса пароля)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend # Для разработки: выводит письма в консоль
# EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend # Для продакшена
# EMAIL_HOST=smtp.example.com
# EMAIL_PORT=587
# EMAIL_USE_TLS=True
# EMAIL_HOST_USER=your_email@example.com
# EMAIL_HOST_PASSWORD=your_email_password
```

**Важно:**

- Замените YOUR_TELEGRAM_BOT_TOKEN на токен вашего Telegram-бота, полученный от BotFather.
- BASE_URL будет URL, предоставленный ngrok.

### 3. Выполнение миграций базы данных

После запуска базы данных выполните миграции:

```
python manage.py makemigrations 
```

```
poetry run python manage.py migrate
```

### 4. Загрузка начальных данных (фикстуры)

Проект включает начальные данные (пользователи, привычки, категории), которые можно загрузить с помощью кастомной
команды:

```
poetry run python manage.py loadinitialdata
```

Эта команда сначала предложит удалить существующие данные. Введите да для подтверждения.

### 5. Запуск Celery Worker и Celery Beat

Celery необходим для выполнения асинхронных задач (например, отправки напоминаний). Запустите их в отдельных терминалах:

Терминал 1: Celery Worker

```
poetry run celery -A config worker -l info -E -P solo
```

Терминал 2: Celery Beat (планировщик)

```
poetry run celery -A config beat -l info -s celerybeat-schedule
```

### 6. Запуск сервера Django

```
poetry run python manage.py runserver
```

Сервер будет доступен по адресу http://127.0.0.1:8000/.

### 7. Настройка Telegram Webhook с Ngrok

Telegram-бот взаимодействует с вашим приложением через вебхуки. Поскольку ваш сервер работает локально,
вам нужно использовать ngrok для создания публичного туннеля:

Терминал 3: Ngrok

```
ngrok http http://localhost:8080 
```

ngrok предоставит публичный URL (например, https://abcdef123456.ngrok-free.app). Скопируйте этот URL.

**Установите вебхук Telegram:**

Отправьте HTTP POST-запрос на Telegram Bot API для установки вебхука. Замените <YOUR_TELEGRAM_BOT_TOKEN> на ваш токен,
а <YOUR_NGROK_URL> на URL, который предоставил ngrok:

```
curl -F "url=<YOUR_NGROK_URL>/telegram/webhook/" https://api.telegram.org/bot<YOUR_TELEGRAM_BOT_TOKEN>/setWebhook
```

Убедитесь, что BASE_URL в вашем .env файле также обновлен до YOUR_NGROK_URL.

Теперь ваш Telegram-бот должен получать обновления и взаимодействовать с вашим приложением.
Попробуйте отправить команду /start вашему боту в Telegram.

## Использование API и бота

**Документация API**
После запуска сервера Django, документация API будет доступна по адресу: http://127.0.0.1:8000/ (или ваш ngrok URL).

Вы можете использовать эту документацию для взаимодействия с API, регистрации новых пользователей, создания привычек и
т.д.

**Telegram-бот**

Чтобы начать использовать бота:

1. Найдите вашего бота в Telegram по имени пользователя (например, @YourHabitBot).
2. Отправьте команду /start.
3. Бот предложит привязать ваш Telegram Chat ID к аккаунту на сайте. Используйте Chat ID, который бот пришлет, и
   обновите профиль пользователя на сайте или через API.
4. После привязки вы будете получать напоминания о привычках и сможете взаимодействовать с ними через кнопки.

## Заключение

GoodHabitLab предоставляет комплексное решение для управления привычками, сочетая удобство веб-интерфейса и
оперативность Telegram-бота. Следуя этим инструкциям, вы сможете запустить проект и начать формировать полезные привычки
уже сегодня!