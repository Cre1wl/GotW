from django.db import models
from worlds.models import World


class ElementType(models.Model):
    """Категория элемента (Персонаж, Локация, Предмет и т.д.)"""

    name = models.CharField(max_length=100, verbose_name="Название категории")
    world = models.ForeignKey(World, on_delete=models.CASCADE, related_name='element_types')
    icon = models.CharField(max_length=50, default='cube', verbose_name="Иконка")
    color = models.CharField(max_length=7, default='#6d28d9', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Категория элемента"
        verbose_name_plural = "Категории элементов"
        unique_together = ['name', 'world']

    def __str__(self):
        return self.name


class Element(models.Model):
    """Элемент мира с динамическими полями"""

    world = models.ForeignKey(World, on_delete=models.CASCADE, related_name='elements')
    element_type = models.ForeignKey(ElementType, on_delete=models.CASCADE, related_name='elements')
    name = models.CharField(max_length=200, verbose_name="Название")

    # Поля элемента хранятся в JSON
    fields_schema = models.JSONField(default=dict, verbose_name="Схема полей")
    data = models.JSONField(default=dict, verbose_name="Данные элемента")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Элемент"
        verbose_name_plural = "Элементы"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.element_type.name})"