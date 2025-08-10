from django.contrib import admin

from .models import User, UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False  # Не разрешаем удалять профиль пользователя
    verbose_name_plural = 'Профиль пользователя'
    fk_name = 'user'


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "telegram_chat_id", "last_active")
    search_fields = ("email",)
    inlines = (UserProfileInline,)

    def get_inline_instances(self, request, obj=None):
        """
        Возвращает экземпляры инлайнов для заданного объекта.
        Создает UserProfile, если он отсутствует, перед отображением инлайна.
        """
        if obj:
            # Проверяем, существует ли уже UserProfile для этого пользователя
            UserProfile.objects.get_or_create(user=obj)
        return super().get_inline_instances(request, obj)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "notify_telegram", "reminder_frequency", "reminder_time", "streak", "rewards_count")
