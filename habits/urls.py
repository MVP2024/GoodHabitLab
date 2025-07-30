from rest_framework.routers import DefaultRouter
from .views import HabitCategoryViewSet, HabitLogViewSet, RewardViewSet, NotificationViewSet, HabitViewSet


router = DefaultRouter()
router.register(r"habits", HabitViewSet, basename="habit")
router.register(r'categories', HabitCategoryViewSet, basename='habitcategory')
router.register(r'habit-logs', HabitLogViewSet, basename='habitlog')
router.register(r'rewards', RewardViewSet, basename='reward')
router.register(r'notifications', NotificationViewSet, basename='notification')

urlpatterns = router.urls
