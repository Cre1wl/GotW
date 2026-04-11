from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings


class LoginRequiredMiddleware:
    """
    Middleware для автоматического перенаправления неавторизованных пользователей
    на страницу входа, кроме разрешенных URL-ов
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # Список URL, которые доступны без авторизации
        self.exempt_urls = [
            reverse('users:login'),
            reverse('users:register'),
            '/admin/',  # Админка доступна
            '/static/',  # Статические файлы
            '/media/',  # Медиа файлы
        ]

    def __call__(self, request):
        if not request.user.is_authenticated:
            # Проверяем, не пытается ли пользователь зайти на разрешенный URL
            path = request.path_info
            if not any(path.startswith(url) for url in self.exempt_urls):
                # Сохраняем URL, куда хотел перейти пользователь
                request.session['next_url'] = path
                return redirect(settings.LOGIN_URL)

        response = self.get_response(request)
        return response