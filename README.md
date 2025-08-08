# GoodHabitLab

![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=green)
![Django REST Framework](https://img.shields.io/badge/DRF-FF1709?style=for-the-badge&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Git](https://img.shields.io/badge/Git-F05032?style=for-the-badge&logo=git&logoColor=white)
![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)

GoodHabitLab — это веб-приложение и Telegram-бот, разработанный для помощи пользователям в формировании и отслеживании
полезных привычек. Проект включает в себя REST API для управления привычками, категории привычек, систему логов
выполнения и уведомлений, а также интеграцию с Telegram для напоминаний и интерактивного взаимодействия.

## Описание проекта

Проект разработан с использованием Django REST Framework для бэкенда и PostgreSQL в качестве базы данных. Для
асинхронной обработки задач и планирования напоминаний используются Celery и Redis. Интеграция с Telegram реализована
через вебхуки и Telegram Bot API, что позволяет пользователям получать напоминания и управлять привычками
непосредственно из мессенджера.

**Ключевые особенности:**

*   **Управление привычками:** Создание, редактирование, удаление, просмотр личных и публичных привычек.
*   **Категории привычек:** Классификация привычек для удобства организации и анализа.
*   **Логи выполнения:** Отслеживание прогресса выполнения привычек с возможностью пометки выполнения и откладывания.
*   **Уведомления Telegram:** Ежедневные напоминания и интерактивные кнопки для действий с привычками через Telegram-бот.
*   **Система вознаграждений:** Возможность устанавливать вознаграждения за выполнение привычек.
*   **Гибкая периодичность:** Поддержка ежедневных, еженедельных, ежемесячных и пользовательских расписаний для привычек.
*   **Аутентификация JWT:** Безопасная аутентификация пользователей с помощью JWT-токенов.
*   **Интерактивная документация API:** Используется `drf-spectacular` для генерации Swagger/OpenAPI документации.

## Технологии

*   **Backend:** Python, Django REST Framework
*   **База данных:** PostgreSQL
*   **Очередь сообщений/Брокер:** Redis
*   **Асинхронные задачи:** Celery, `django-celery-beat`
*   **Telegram Bot API:** Интеграция через вебхуки
*   **Аутентификация:** `djangorestframework-simplejwt`
*   **Документация API:** `drf-spectacular`
*   **Загрузка данных:** `python-dotenv`

## Структура проекта

*   `config/`: Основные настройки проекта Django, корневые URL-адреса, конфигурация Celery.
*   `users/`: Приложение для управления пользователями, их профилями. Содержит модели, сериализаторы, представления,
    URL-адреса и логику для аутентификации.
*   `habits/`: Приложение для управления привычками, их категориями, логами выполнения и наградами. Содержит модели,
    сериализаторы, представления, URL-адреса и Celery задачи для напоминаний.
*   `telegram_bot/`: Приложение для интеграции с Telegram Bot API, обработки вебхуков и отправки сообщений.
*   `media/`: Директория для хранения загружаемых пользователями файлов (аватары, иконки привычек).
*   `.venv/`: Виртуальное окружение Python (игнорируется Git).
*   `.env`, `.env.example`: Файлы для хранения переменных окружения.
*   `requirements.txt`: Список всех зависимостей проекта.
*   `manage.py`: Утилита командной строки Django для выполнения административных задач.
*   `celerybeat-schedule*`: Файлы, используемые Celery Beat для хранения состояния расписания задач (игнорируются Git).

## Запуск проекта

Для успешного запуска проекта вам потребуются:

*   **Python 3.10+**
*   **pip** (для управления зависимостями)
*   **PostgreSQL** (установленный локально)
*   **Redis** (установленный локально)
*   **ngrok** (для туннелирования локального сервера Telegram вебхукам)

## Установка и запуск

Следуйте этим шагам, чтобы настроить и запустить проект локально.

### 2. Создание и активация виртуального окружения

Следуйте этим шагам, чтобы настроить и запустить проект локально.

### 1. Клонирование репозитория и установка зависимостей

    ```
        git clone <URL вашего репозитория>
        cd GoodHabitLab
        pip install -r requirements.txt
    ```


### 2. Создание и активация виртуального окружения

Рекомендуется использовать виртуальное окружение для изоляции зависимостей проекта.

Для Windows:

    ```
        python -m venv .venv
        .venv\Scripts\activate
    ```

Для macOS/Linux:
    
    ```
        python3 -m venv .venv
        source .venv/bin/activate
    ```


### 3. Установка зависимостей

Установите все необходимые библиотеки из requirements.txt:

    ```
        pip install -r requirements.txt
    ```


### 4. Настройка переменных окружения

Создайте файл `.env` в корне проекта на основе `.env.example` и заполните его необходимыми значениями.
Обязательно укажите:

### .env

*   SECRET_KEY=your_django_secret_key
*   DEBUG=True
*   ALLOWED_HOSTS=127.0.0.1,localhost

**Настройки ДБ (PostgreSQL)**

*   DB_NAME=goodhabitlab_db
*   DB_USER=goodhabitlab_user
*   DB_PASSWORD=goodhabitlab_password
*   DB_HOST=localhost
*   DB_PORT=5432

*   **Настройки Redis для Celery**:
*   CELERY_BROKER_URL=redis://localhost:6379/0
*   CELERY_RESULT_BACKEND=redis://localhost:6379/0

**Telegram Bot API**

*   TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
*   TELEGRAM_CHAT_ID=YOUR_TELEGRAM_CHAT_ID # (опционально, для тестовых отправок)
*   BASE_URL=http://your_ngrok_url # Пример: https://abcdef123456.ngrok-free.app

**Важно:**

-   Замените YOUR_TELEGRAM_BOT_TOKEN на токен вашего Telegram-бота, полученный от BotFather.
-   BASE_URL будет URL, предоставленный ngrok.

**Настройка Email (для сброса пароля)**

*   EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend # Для разработки: выводит письма в консоль
*   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend # Для продакшен
*   EMAIL_HOST=smtp.example.com
*   EMAIL_PORT=587
*   EMAIL_USE_TLS=True
*   EMAIL_HOST_USER=your_email@example.com
*   EMAIL_HOST_PASSWORD=your_email_password

### 5. Настройка базы данных

Проект использует PostgreSQL. Убедитесь, что у вас установлен и запущен PostgreSQL,
и создайте базу данных, указанную в .env.

### 6. Выполнение миграций

После любых изменений в моделях Django необходимо создать файлы миграций,
а затем применить их для обновления структуры базы данных.

**Создание файлов миграций:**
    
    ```
        python manage.py makemigrations
    ```

**Примените миграции для создания таблиц в базе данных:**

     ```
        python manage.py migrate
     ```


### 7. Загрузка начальных данных (фикстуры)

**Проект включает начальные данные (пользователи, привычки, категории),
которые можно загрузить с помощью кастомной команды:**
    
    ```
        python -Xutf8 manage.py loadinitialdata
    ```

**Эта команда сначала предложит удалить существующие данные. Введите да для подтверждения.
Чтобы создать фикстуру с уже имеющимися у Вас данными, используйте это:**

    ```
        python manage.py dumpdata users.user users.userprofile habits.habitcategory habits.habit --indent 4 > habits/fixtures/initial_data.json
    ```


### 8. Создание суперпользователя (для доступа к админ-панели)

    ```
       python manage.py createsuperuser 
    ```


Следуйте инструкциям в консоли для создания учетной записи суперпользователя.

### 9. Установка и запуск Redis

Redis требуется для работы кеширования (настроен в `settings.py` через `CACHES`).

## Установка

**Windows**:

1.  Скачайте Redis с [официального репозитория](https://github.com/microsoftarchive/redis/releases)
2.  Установите через установщик или запустите `redis-server.exe` напрямую


## Запуск

**Windows:**
    ```
        redis-server.exe
    ```



**Linux**:

    ```
        sudo apt update
        sudo apt install redis
    ```


## Проверка

    ```
        redis-cli ping
    ```
# Ожидаемый ответ: PONG


Убедитесь, что сервер Redis запущен перед запуском приложения.

Сервер будет доступен по адресу http://127.0.0.1:8000/.

### 10. Запуск Celery Worker и Celery Beat

Celery необходим для выполнения асинхронных задач (например, отправки напоминаний).
Запустите их в отдельных терминалах:

**Терминал 1: Celery Worker**

Откройте новый терминал и запустите Celery Worker. На Windows обязательно используйте флаг -P solo для однопоточного
режима, чтобы избежать проблем с многопроцессорностью.

# На Windows
    ```
        celery -A config worker -l info -E -P solo
    ```
# На Linux/macOS
    ```
        celery -A config worker -l info -E
    ```


**Терминал 2: Celery Beat (планировщик)**

Откройте еще один новый терминал и запустите Celery Beat. Он будет планировать периодические задачи.

    ```
        celery -A config beat -l info
    ```


### 11. Запуск сервера Django

    ```
        python manage.py runserver
    ```


Сервер будет доступен по адресу http://127.0.0.1:8000/.

### 12. Как создать Telegram-бота и получить Chat ID

Чтобы ваш проект мог взаимодействовать с Telegram, вам потребуется создать бота и получить его токен,
а также узнать свой персональный Chat ID для тестирования.

#### 1. Создание нового бота через BotFather

1.  Откройте Telegram и найдите бота `@BotFather`. Это официальный бот для управления другими ботами.
2.  Начните диалог с ним, отправив команду `/start`.
3.  Отправьте команду `/newbot`.
4.  BotFather попросит вас выбрать имя для вашего бота. Это отображаемое имя (например, `GoodHabitLab Bot`). Введите его.
5.  Затем BotFather попросит выбрать уникальный username для вашего бота. Он должен заканчиваться на `bot` (например, `GoodHabitLab_test_bot` или `my_awesome_project_bot`). Введите его.
6.  Если username свободен, BotFather пришлет вам сообщение с токеном вашего нового бота.
7.  **Обязательно сохраните этот токен!** Он выглядит примерно так: `123456789:ABCDefgh1234567890abcdef1234567890`.

    Этот токен нужно будет добавить в ваш файл [.env](.env) как значение для `TELEGRAM_BOT_TOKEN`.

#### 2. Получение вашего Telegram Chat ID

Ваш Telegram Chat ID — это уникальный идентификатор вашего личного чата с ботом.
Он необходим, чтобы бот мог отправлять вам сообщения.

1.  Найдите вашего только что созданного бота в Telegram по username (тот, что заканчивается на `bot`).
2.  Начните диалог с ним, отправив любое сообщение, например, `/start`.
3.  Теперь вам нужно узнать `chat_id` этого диалога. Для этого откройте в браузере следующую ссылку,
4.  заменив `<YOUR_BOT_TOKEN>` на токен вашего бота:
    `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
5.  Вы увидите JSON-ответ. Найдите в нем секцию `result` -> `message` -> `chat` -> `id`.
6.  Значение поля `id` будет вашим `telegram_chat_id`. Например:
    ```json
    {
    "ok": true,
    "result": [
      {
        "update_id": 123456789,
        "message": {"message_id": 123,
        "from": {// ...
      },
    "chat": {
        "id": 1234567890,
        "first_name": "ВашеИмя"
            }
        }
        }
            ]
        }
    ```
    
**Если вы видите пустой result массив [],
убедитесь, что вы отправили сообщение боту после его создания, и обновите страницу.**

1. Скопируйте полученный `id` и добавьте его в ваш файл `📄.env` как значение для `TELEGRAM_CHAT_ID`.

**Теперь у вас есть все необходимые данные для настройки Telegram-бота в вашем проекте!**

### 13. Настройка Telegram Webhook с Ngrok

Telegram-бот взаимодействует с вашим приложением через вебхуки. Поскольку ваш сервер работает локально,
вам нужно использовать ngrok для создания публичного туннеля.


1. Зарегистрируйтесь и установите ngrok:

- Перейдите на ngrok.com и зарегистрируйтесь.
- Скачайте ngrok для вашей операционной системы.
- Распакуйте архив и добавьте исполняемый файл ngrok в PATH вашей системы, чтобы он был доступен из любого каталога.

2. Аутентифицируйте ngrok:

- После регистрации на сайте `ngrok.com` вы найдете свой аутентификационный токен в личном кабинете.
- Выполните следующую команду в терминале, заменив `<YOUR_NGROK_AUTHTOKEN>` на ваш реальный токен:
    
    ``` 
        ngrok authtoken <YOUR_NGROK_AUTHTOKEN>
    ```

3. Запустите ngrok:

- В новом терминале запустите ngrok, чтобы создать туннель для вашего локального сервера Django
- (который работает на порту 8000):

    ```
        ngrok http 8000
    ```

- ngrok предоставит публичный URL (например, https://abcdef123456.ngrok-free.app). Скопируйте этот URL.

4. Установите вебхук Telegram:

- Обновите значение `BASE_URL` в вашем файле `📄.env` на скопированный `URL` от `ngrok`.
- Отправьте HTTP POST-запрос на `Telegram Bot API` для установки вебхука. Замените `<YOUR_TELEGRAM_BOT_TOKEN>` на ваш токен,
- а `<YOUR_NGROK_URL>` на URL, который предоставил ngrok (включая /telegram/webhook/):

    ```
        curl -F "url=<YOUR_NGROK_URL>/telegram/webhook/" https://api.telegram.org/bot<YOUR_TELEGRAM_BOT_TOKEN>/setWebhook
    ```
Теперь ваш Telegram-бот должен получать обновления и взаимодействовать с вашим приложением.

## Использование API и бота

**Документация API**
После запуска сервера Django, документация API будет доступна по адресу: http://127.0.0.1:8000/.

Вы можете использовать эту документацию для взаимодействия с API, регистрации новых пользователей, создания привычек и
т.д.


### 14. Регистрация пользователя

**URL:** /api/v1/users/register/
**Метод:** POST
**Headers:** Content-Type: application/json

    ```
        curl -X POST \
          http://127.0.0.1:8000/api/v1/users/register/ \
          -H 'Content-Type: application/json' \
          -d '{
          "email": "your_email@example.com",
          "password": "your_strong_password",
          "telegram_chat_id": "your_telegram_chat_id"
      }'
    ```
**Пример успешного ответа (201 Created):**

    ```
    {
      "message": "Пользователь успешно зарегистрирован."
    }
    ```

### 15. Получение JWT-токенов (авторизация)

**URL:** /api/v1/users/token/
**Метод:** POST
**Headers:** Content-Type: application/json

    ```
        curl -X POST \
      http://127.0.0.1:8000/api/v1/users/token/ \
      -H 'Content-Type: application/json' \
      -d '{
        "email": "your_email@example.com",
        "password": "your_strong_password"
      }'
    ```

**Пример успешного ответа (200 OK):**

    ```
    {
      "refresh": "eyJhbGciOiJIUzI1Ni...",
      "access": "eyJhbGciOiJIUzI1Ni...",
      "id": 1,
      "email": "your_email@example.com",
      "telegram_chat_id": "your_telegram_chat_id"
    }
    ```

### 16. Обновление access-токена

**URL:** /api/v1/users/token/refresh/
**Метод:** POST
**Headers:** Content-Type: application/json

    ```
        curl -X POST \
      http://127.0.0.1:8000/api/v1/users/token/refresh/ \
      -H 'Content-Type: application/json' \
      -d '{
        "refresh": "eyJhbGciOiJIUzI1Ni..."
      }'
    ```

**Пример успешного ответа (200 OK):**

    ```
    {
      "access": "eyJhbGciOiJIUzI1Ni...",
      "refresh": "eyJhbGciOiJIUzI1Ni..."
    }
    ```

### 17. Просмотр своего профиля

**URL:** /api/v1/users/profile/<user_id>/ (замените <user_id> на свой ID пользователя из токена)
**Метод:** GET
**Headers:** Authorization: Bearer <your_access_token>
    ```
    curl -X GET \
      http://127.0.0.1:8000/api/v1/users/profile/1/ \
      -H 'Authorization: Bearer <your_access_token>'
    ```
**Пример успешного ответа (200 OK):**
    ```
    json
    {
      "id": 1,
      "email": "your_email@example.com",
      "telegram_chat_id": "your_telegram_chat_id"
    }
    ```

### 18. Частичное обновление профиля (например, telegram_chat_id)

**URL:** /api/v1/users/profile/<user_id>/
**Метод:** PATCH
**Headers:**

Authorization: Bearer <your_access_token>
Content-Type: application/json

    ```
    curl -X PATCH \
      http://127.0.0.1:8000/api/v1/users/profile/1/ \
      -H 'Authorization: Bearer <your_access_token>' \
      -H 'Content-Type: application/json' \
      -d '{
        "telegram_chat_id": "new_telegram_chat_id"
      }'
    ```
**Пример успешного ответа (200 OK):**
    ```
    {
      "id": 1,
      "email": "your_email@example.com",
      "telegram_chat_id": "new_telegram_chat_id"
    }
    ```

### 19. Запрос на сброс пароля

**URL:** /api/v1/users/password_reset/
**Метод:** POST
**Headers:** Content-Type: application/json
    ```
    curl -X POST \
      http://127.0.0.1:8000/api/v1/users/password_reset/ \
      -H 'Content-Type: application/json' \
      -d '{
        "email": "your_registered_email@example.com"
      }'
    ```
**Пример успешного ответа (200 OK):**
    ```
    {
      "detail": "Инструкции по сбросу пароля отправлены на ваш email."
    }
    ```
### 20. Подтверждение сброса пароля (установка нового)

После получения письма со ссылкой для сброса пароля, извлеките uidb64 и token из этой ссылки.

**URL:** /api/v1/users/password_reset/confirm/<uidb64>/<token>/
**Метод:** POST
**Headers:** Content-Type: application/json
    ```
    curl -X POST \
      http://127.0.0.1:8000/api/v1/users/password_reset/confirm/MzI/b8c7r6y-d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6/ \
      -H 'Content-Type: application/json' \
      -d '{
        "new_password1": "new_strong_password",
        "new_password2": "new_strong_password"
      }'
    ```
**Пример успешного ответа (200 OK):**
    ```
    {
      "detail": "Пароль успешно изменен."
    }
    ```

### Telegram-бот

Чтобы начать использовать бота:

1. Найдите вашего бота в Telegram по имени пользователя (например, @YourHabitBot).
2. Отправьте команду /start. Бот предложит привязать ваш Telegram Chat ID к аккаунту на сайте.
3. Используйте Chat ID, который бот пришлет, и обновите профиль пользователя на сайте или через API (см. пункт 18 выше).
4. После привязки вы будете получать напоминания о привычках.

### Тестирование

Проект покрыт автоматическими тестами с использованием pytest.

**Установка**

Для запуска тестов необходимо установить pytest и pytest-cov:
    ```
        pip install pytest pytest-cov
    ```

**Запуск тестов и генерация отчета о покрытии кода**

Для запуска всех тестов и генерации отчета о покрытии кода:

    ```
        pytest --cov=users --cov=telegram_bot --cov=habits --cov-report=html
    ```
После выполнения этой команды будет сгенерирован HTML-отчет в папке `htmlcov/`.
Откройте файл `htmlcov/index.html` в
браузере, чтобы просмотреть подробный отчет о покрытии кода.


**Запуск отдельного теста**

Чтобы запустить конкретный тест, например `test_poll_inactive_users` в файле
`telegram_bot/tests/test_telegram_bot_tasks.py`:

    ```
        python manage.py test telegram_bot.tests.test_telegram_bot_tasks.TelegramTasksTestCase.test_poll_inactive_users
    ```
## Заключение

GoodHabitLab предоставляет комплексное решение для управления привычками, сочетая удобство веб-интерфейса и
оперативность Telegram-бота. Следуя этим инструкциям, вы сможете запустить проект и начать формировать полезные привычки
уже сегодня!
