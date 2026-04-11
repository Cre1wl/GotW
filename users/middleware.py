from django.utils import timezone
from django.contrib.auth.models import AnonymousUser


class UpdateLastActivityMiddleware:
    """Middleware для обновления времени последней активности пользователя"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Обновляем активность для авторизованных пользователей
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Обновляем не чаще чем раз в минуту
            now = timezone.now()
            if hasattr(request.user, 'last_activity'):
                if not request.user.last_activity or (now - request.user.last_activity).total_seconds() > 60:
                    request.user.last_activity = now
                    request.user.save(update_fields=['last_activity'])

        return response