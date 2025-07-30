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
        if self.instance and self.instance.selected_weekdays:
            self.initial['selected_weekdays'] = self.instance.selected_weekdays

    def clean(self):
        cleaned_data = super().clean()
        periodicity = cleaned_data.get('periodicity')
        selected_weekdays = cleaned_data.get('selected_weekdays')

        if periodicity == 'custom' and not selected_weekdays:
            self.add_error('selected_weekdays', "Для 'Выборочных дней' необходимо выбрать хотя бы один день недели.")
        elif periodicity != 'custom':
            # Если выбрана не 'custom' периодичность, очищаем selected_weekdays
            # Это должно быть так, потому что для других периодичностей дни недели неактуальны.
            cleaned_data['selected_weekdays'] = []

        # Автоматическое переключение на "Ежедневно", если выбраны все 7 дней в custom
        if periodicity == 'custom' and selected_weekdays and len(selected_weekdays) == 7:
            cleaned_data['periodicity'] = 'daily'
            cleaned_data['selected_weekdays'] = [] # Очищаем, так как теперь daily

        return cleaned_data
