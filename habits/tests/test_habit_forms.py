from django.test import TestCase

from habits.forms import HabitAdminForm
from habits.models import Habit, HabitCategory
from users.models import User


class HabitAdminFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(email='test@example.com')
        self.category = HabitCategory.objects.create(name='Здоровье')

    def test_daily_periodicity_fills_all_weekdays(self):
        """Проверка, что при периодичности 'daily' заполняются все дни недели."""
        form_data = {
            'periodicity': 'daily',
            'title': 'Пить воду',
            'user': self.user.id,
            'place': 'Офис',
            'duration': 15,
            'category': self.category.id,
            'planned_time': '10:00:00'
        }
        form = HabitAdminForm(data=form_data)
        self.assertTrue(form.is_valid())
        all_weekdays = [day[0] for day in form.fields['selected_weekdays'].choices]
        self.assertEqual(form.cleaned_data['selected_weekdays'], all_weekdays)

    def test_form_saves_daily_habit_correctly(self):
        """Проверка сохранения привычки с периодичностью 'daily'."""
        form_data = {
            'periodicity': 'daily',
            'title': 'Утренняя зарядка',
            'user': self.user.id,
            'place': 'Дом',
            'duration': 30,
            'category': self.category.id,
            'planned_time': '07:00:00'
        }
        form = HabitAdminForm(data=form_data)
        self.assertTrue(form.is_valid())
        habit = form.save()
        self.assertEqual(habit.periodicity, 'daily')
        all_weekdays = [day[0] for day in form.fields['selected_weekdays'].choices]
        self.assertEqual(habit.selected_weekdays, all_weekdays)

    def test_custom_periodicity_with_duplicates(self):
        """Проверка формы с кастомной периодичностью и дубликатами дней."""
        form_data = {
            'periodicity': 'custom',
            'selected_weekdays': ['пн', 'вт', 'пн', 'ср', 'вт'],  # Дубликаты
            'title': 'Занятия спортом',
            'user': self.user.id,
            'place': 'Спортзал',
            'duration': 45,
            'category': self.category.id,
            'planned_time': '18:00:00'
        }
        form = HabitAdminForm(data=form_data)
        self.assertTrue(form.is_valid())
        # После очистки дубликатов должно остаться уникальное множество дней
        expected_days = ['пн', 'вт', 'ср']  # Порядок может отличаться
        self.assertListEqual(sorted(form.cleaned_data['selected_weekdays']), sorted(expected_days))

    def test_form_saves_custom_habit_correctly(self):
        """Проверка сохранения привычки с кастомной периодичностью."""
        form_data = {
            'periodicity': 'custom',
            'selected_weekdays': ['вт', 'чт', 'сб'],
            'title': 'Прогулка на свежем воздухе',
            'user': self.user.id,
            'place': 'Парк',
            'duration': 60,
            'category': self.category.id,
            'planned_time': '15:00:00'
        }
        form = HabitAdminForm(data=form_data)
        self.assertTrue(form.is_valid())
        habit = form.save()
        self.assertEqual(habit.periodicity, 'custom')
        self.assertEqual(habit.title, 'Прогулка на свежем воздухе')
        expected_days = ['вт', 'чт', 'сб']
        self.assertListEqual(sorted(habit.selected_weekdays), sorted(expected_days))