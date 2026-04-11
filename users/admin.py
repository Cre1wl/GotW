from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


class CustomUserAdmin(UserAdmin):
    """Кастомизация админки пользователей"""

    list_display = ('username', 'email', 'first_name', 'last_name',
                    'is_active', 'date_joined', 'last_activity')
    list_filter = ('is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')

    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {
            'fields': ('avatar', 'bio', 'location', 'birth_date',
                       'website', 'telegram', 'github', 'twitter')
        }),
        ('Статистика', {
            'fields': ('worlds_count', 'elements_count', 'last_activity')
        }),
        ('Настройки', {
            'fields': ('email_notifications',)
        }),
    )

    readonly_fields = ('worlds_count', 'elements_count', 'last_activity')


admin.site.register(CustomUser, CustomUserAdmin)