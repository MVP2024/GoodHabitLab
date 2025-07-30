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


# @admin.register(Admin)
# class AdminAdmin(admin.ModelAdmin):
#     list_display = ("user", "notify_telegram", "reminder_frequency", "reminder_time", "streak", "rewards_count")
#
#     def get_queryset(self, request):
#         return super().get_queryset(request).filter(is_staff=True)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "notify_telegram", "reminder_frequency", "reminder_time", "streak", "rewards_count")
