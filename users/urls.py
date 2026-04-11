from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Landing page для неавторизованных
    path('', views.landing_view, name='landing'),

    # Регистрация и авторизация
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Восстановление пароля
    path('password-reset/', views.password_reset_request_view, name='password_reset'),
    path('password-reset/done/', views.password_reset_done_view, name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.password_reset_confirm_view, name='password_reset_confirm'),
    path('reset/done/', views.password_reset_complete_view, name='password_reset_complete'),

    # Профиль
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('profile/password-change/', views.password_change_view, name='password_change'),
    path('profile/delete-account/', views.delete_account_view, name='delete_account'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/<str:username>/', views.profile_view, name='profile_detail'),
]