import os

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Загружает все данные из общей фикстуры habits/fixtures/initial_data.json.'

    def handle(self, *args, **kwargs):
        fixture_path = os.path.join(settings.BASE_DIR, 'habits', 'fixtures', 'initial_data.json')
        self.stdout.write(self.style.NOTICE('Запуск команды загрузки общей фикстуры...'))
        if not os.path.exists(fixture_path):
            self.stdout.write(self.style.ERROR(f'Фикстура не найдена по пути {fixture_path}'))
            return
        self.stdout.write(self.style.WARNING(
            'Внимание: Будут удалены существующие данные перед загрузкой фикстуры. Продолжить? (да/нет)'))
        confirm = input("Введите 'да' для продолжения или 'нет' для отмены:")
        if confirm.lower() == 'да':
            try:
                self.stdout.write(self.style.NOTICE('Удаление существующих данных из базы данных...'))
                call_command('flush', '--noinput')
                self.stdout.write(self.style.SUCCESS('Существующие данные успешно удалены.'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Ошибка при удалении данных: {e}"))
                return
        elif confirm.lower() == 'нет':
            self.stdout.write(self.style.NOTICE('Загрузка фикстур отменена пользователем.'))
            return
        try:
            call_command('loaddata', fixture_path)
            self.stdout.write(self.style.SUCCESS("Данные успешно загружены из фикстуры."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка при загрузке данных: {e}"))
