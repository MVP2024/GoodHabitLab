from django.contrib import admin

from .forms import HabitAdminForm
from .models import Habit, HabitCategory, HabitLog, Notification, Reward


@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    form = HabitAdminForm
    list_display = (
        "user",
        "title",
        "description",
        "category",
        "is_public",
        "periodicity",
        "planned_time",
        "color",
        "icon",
        "created_at",
        "updated_at",
        "place",
    )
    list_filter = ("is_public", "periodicity", "category", "user")
    search_fields = ("title", "description", "category__name", "user__email")


@admin.register(HabitCategory)
class HabitCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "description")
    search_fields = ("name",)


@admin.register(HabitLog)
class HabitLogAdmin(admin.ModelAdmin):
    list_display = ("habit", "date", "is_done", "user", "last_reminded_at")
    list_filter = ("is_done", "habit__category", "user")
    search_fields = ("habit__title", "user__email")


@admin.register(Reward)
class RewardAdmin(admin.ModelAdmin):
    list_display = ("habit", "description", "created_at", "user")
    list_filter = ("habit__category", "user")
    search_fields = ("habit__title", "description", "user__email")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "habit", "channel", "sent_at", "notification_type", "notification_title")
    list_filter = ("channel", "user", "notification_type")
    # Добавляем notification_type для редактирования/создания в админке
    fields = ("user", "habit", "channel", "notification_type", "notification_title", "message")
