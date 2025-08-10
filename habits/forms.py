from django import forms

from .models import Habit


class HabitAdminForm(forms.ModelForm):
    selected_weekdays = forms.MultipleChoiceField(
        choices=[
            ('пн', 'Понедельник'),
            ('вт', 'Вторник'),
            ('ср', 'Среда'),
            ('чт', 'Четверг'),
            ('пт', 'Пятница'),
            ('сб', 'Суббота'),
            ('вс', 'Воскресенье'),
        ],
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Выбранные дни недели"
    )

    class Meta:
        model = Habit
        fields = [
            "user",
            "title",
            "description",
            "category",
            "is_public",
            "periodicity",
            "selected_weekdays",
            "planned_time",
            "color",
            "icon",
            "is_active",
            "place",
            "is_pleasant",
            "duration",
            "reward",
            "related_habit",
        ]
        widgets = {
            'icon': forms.TextInput(
                attrs={'placeholder': 'Выберите эмодзи, например: 😊'}
            ),
            'planned_time': forms.TimeInput(
                attrs={'placeholder': 'Введите время в формате, например: 22:00', 'type': 'time'}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.periodicity == 'daily':
            # Если periodic_type 'daily', то selected_weekdays должны быть все дни
            self.initial['selected_weekdays'] = [day[0] for day in self.fields['selected_weekdays'].choices]
        elif self.instance and self.instance.selected_weekdays:
            self.initial['selected_weekdays'] = self.instance.selected_weekdays

    def clean(self):
        cleaned_data = super().clean()
        periodicity = cleaned_data.get('periodicity')
        selected_weekdays = cleaned_data.get('selected_weekdays')

        # Если периодичность 'daily', автоматически заполняем selected_weekdays всеми днями недели.
        # Это также обработает случай, когда пользователь выбрал 'daily', но не выбрал дни.
        if periodicity == 'daily':
            all_weekdays = [day[0] for day in self.fields['selected_weekdays'].choices]
            cleaned_data['selected_weekdays'] = all_weekdays
        elif periodicity == 'custom':
            if not selected_weekdays:
                self.add_error('selected_weekdays',
                               "Для 'Выборочных дней' необходимо выбрать хотя бы один день недели.")
            # Убираем дубликаты дней недели, если есть
            cleaned_data['selected_weekdays'] = list(set(selected_weekdays))
        else:
            # Если выбрана не 'custom' и не 'daily' периодичность, очищаем selected_weekdays
            cleaned_data['selected_weekdays'] = []

        return cleaned_data
