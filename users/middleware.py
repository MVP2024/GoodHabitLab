from django.utils import timezone


class LastActiveMiddleware:
    """
    Middleware для автоматического обновления last_active при каждом запросе пользователя.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Проверяем — залогинен ли пользователь
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            user.last_active = timezone.now()
            user.save(update_fields=["last_active"])
        response = self.get_response(request)
        return response
