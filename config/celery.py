import os
from celery import Celery

# Устанавливаем переменную окружения по умолчанию для настроек Django.
# Это необходимо, чтобы Celery мог получить доступ к вашим настройкам Django.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Создаем экземпляр приложения Celery.
app = Celery('GoodHabitLab')

# Используем настройки Django для конфигурации Celery.
# Это означает, что все настройки Celery будут браться из файла settings.py вашего Django проекта,
# если они начинаются с префикса 'CELERY_'.
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """
    Простая отладочная задача, которая выводит информацию о запросе.
    Используется для проверки работоспособности Celery.
    """
    print(f"Запрос: {self.request!r}")
