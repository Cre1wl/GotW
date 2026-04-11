from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),  # Главная страница
    path('users/', include('users.urls')),
    path('worlds/', include('worlds.urls')),
    path('elements/', include('elements.urls')),
    path('galleries/', include('galleries.urls')),
    path('relationships/', include('relationships.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)