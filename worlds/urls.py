from django.urls import path
from . import views

app_name = 'worlds'

urlpatterns = [
    # Основные страницы
    path('', views.library, name='library'),
    path('create/', views.world_create, name='world_create'),

    # Управление миром
    path('<int:world_id>/', views.world_detail, name='world_detail'),
    path('<int:world_id>/settings/', views.world_settings, name='world_settings'),
    path('<int:world_id>/delete/', views.world_delete, name='world_delete'),
    path('<int:world_id>/dashboard/', views.world_dashboard, name='world_dashboard'),
]