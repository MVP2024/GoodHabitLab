from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (HabitCategoryViewSet, HabitLogViewSet, HabitViewSet,
                    NotificationViewSet, RewardViewSet)

app_name = 'habits'

router = DefaultRouter()
router.register(r'habits', HabitViewSet, basename='habits')
router.register(r'categories', HabitCategoryViewSet, basename='categories')
router.register(r'logs', HabitLogViewSet, basename='logs')
router.register(r'rewards', RewardViewSet, basename='rewards')
router.register(r'notifications', NotificationViewSet, basename='notifications')

urlpatterns = [
    path('', include(router.urls)),
    path('habits/<int:pk>/copy/', HabitViewSet.as_view({'post': 'copy'}), name='habit-copy'),
]
