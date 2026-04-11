from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator

User = get_user_model()


class Gallery(models.Model):
    """Галерея для сущности (может принадлежать любому объекту)"""

    name = models.CharField(max_length=200, verbose_name="Название галереи")
    description = models.TextField(blank=True, verbose_name="Описание")

    # Generic relation для связи с любой моделью (World, Element и т.д.)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    # Настройки галереи
    is_public = models.BooleanField(default=True, verbose_name="Публичная галерея")
    max_images = models.IntegerField(default=50, verbose_name="Максимум изображений")

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_galleries')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Галерея"
        verbose_name_plural = "Галереи"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f"{self.name} - {self.content_type.model} #{self.object_id}"

    def get_primary_image(self):
        """Получить основное изображение галереи"""
        return self.images.filter(is_primary=True).first()

    def get_images_count(self):
        """Получить количество изображений"""
        return self.images.count()

    def can_add_image(self):
        """Проверить, можно ли добавить новое изображение"""
        return self.images.count() < self.max_images


class GalleryImage(models.Model):
    """Отдельное изображение в галерее"""

    gallery = models.ForeignKey(
        Gallery,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name="Галерея"
    )

    image = models.ImageField(
        upload_to='gallery_images/%Y/%m/%d/',
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'gif', 'webp'])],
        verbose_name="Изображение"
    )

    title = models.CharField(max_length=200, blank=True, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    alt_text = models.CharField(max_length=200, blank=True, verbose_name="Alt текст")

    order = models.IntegerField(default=0, verbose_name="Порядок")
    is_primary = models.BooleanField(default=False, verbose_name="Основное изображение")

    # Метаданные
    file_size = models.IntegerField(default=0, verbose_name="Размер файла (байты)")
    file_type = models.CharField(max_length=50, blank=True, verbose_name="Тип файла")
    width = models.IntegerField(default=0, verbose_name="Ширина")
    height = models.IntegerField(default=0, verbose_name="Высота")

    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Загрузил")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Изображение"
        verbose_name_plural = "Изображения"
        ordering = ['order', '-uploaded_at']
        indexes = [
            models.Index(fields=['gallery', 'order']),
            models.Index(fields=['is_primary']),
        ]

    def __str__(self):
        return self.title or f"Image {self.id}"

    def save(self, *args, **kwargs):
        # Обеспечиваем только одно основное изображение на галерею
        if self.is_primary:
            GalleryImage.objects.filter(gallery=self.gallery, is_primary=True).exclude(id=self.id).update(
                is_primary=False)

        # Получаем информацию об изображении
        if self.image and not self.pk:
            from PIL import Image
            import os
            try:
                img = Image.open(self.image.path)
                self.width, self.height = img.size
                self.file_size = os.path.getsize(self.image.path)
                self.file_type = self.image.name.split('.')[-1].upper()
            except:
                pass

        super().save(*args, **kwargs)

    def get_thumbnail_url(self, size='medium'):
        """Получить URL миниатюры (можно расширить для работы с sorl-thumbnail)"""
        return self.image.url

    def delete(self, *args, **kwargs):
        # Удаляем файл изображения
        self.image.delete(save=False)
        super().delete(*args, **kwargs)