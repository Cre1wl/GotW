from django.contrib import admin
from .models import World


@admin.register(World)
class WorldAdmin(admin.ModelAdmin):
    list_display = ['name', 'creator', 'elements_count', 'categories_count', 'created_at']
    list_filter = ['creator', 'created_at']
    search_fields = ['name', 'creator__username', 'description']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'cover_image', 'creator')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def elements_count(self, obj):
        return obj.elements.count()

    elements_count.short_description = 'Элементов'

    def categories_count(self, obj):
        return obj.element_types.count()

    categories_count.short_description = 'Категорий'