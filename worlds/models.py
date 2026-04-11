from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class World(models.Model):
    """Модель мира"""

    name = models.CharField(max_length=200, verbose_name="Название мира")
    description = models.TextField(verbose_name="Описание")
    cover_image = models.ImageField(
        upload_to='world_covers/%Y/%m/%d/',
        null=True,
        blank=True,
        verbose_name="Обложка мира"
    )
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='worlds')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Мир"
        verbose_name_plural = "Миры"
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('worlds:world_detail', args=[self.id])