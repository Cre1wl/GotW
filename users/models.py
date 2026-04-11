from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class CustomUser(AbstractUser):
    """Расширенная модель пользователя"""

    # Дополнительные поля профиля
    avatar = models.ImageField(
        upload_to='avatars/%Y/%m/%d/',
        null=True,
        blank=True,
        verbose_name="Аватар"
    )
    bio = models.TextField(
        max_length=500,
        blank=True,
        verbose_name="О себе"
    )
    website = models.URLField(
        blank=True,
        verbose_name="Сайт"
    )
    location = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Местоположение"
    )
    birth_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Дата рождения"
    )

    # Социальные сети
    telegram = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Telegram"
    )
    github = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="GitHub"
    )
    twitter = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Twitter/X"
    )

    # Статистика
    worlds_count = models.IntegerField(
        default=0,
        verbose_name="Количество миров"
    )
    elements_count = models.IntegerField(
        default=0,
        verbose_name="Количество элементов"
    )
    last_activity = models.DateTimeField(
        default=timezone.now,
        verbose_name="Последняя активность"
    )

    # Настройки уведомлений
    email_notifications = models.BooleanField(
        default=True,
        verbose_name="Email уведомления"
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ['-date_joined']

    def __str__(self):
        return self.username

    def get_full_name(self):
        """Полное имя пользователя"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username

    def get_last_activity_display(self):
        """Возвращает отформатированное время последней активности"""
        if not self.last_activity:
            return "Никогда"

        now = timezone.now()
        diff = now - self.last_activity

        if diff.days > 7:
            return self.last_activity.strftime("%d.%m.%Y")
        elif diff.days > 0:
            return f"{diff.days} дн. назад"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} ч. назад"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} мин. назад"
        else:
            return "Только что"

    def is_online(self):
        """Проверяет, онлайн ли пользователь (активен в последние 5 минут)"""
        if not self.last_activity:
            return False
        now = timezone.now()
        diff = now - self.last_activity
        return diff.total_seconds() < 300

    def update_stats(self):
        """Обновление статистики пользователя"""
        self.worlds_count = self.worlds.count()
        # self.elements_count = self.created_elements.count()
        self.save(update_fields=['worlds_count', 'elements_count'])