from django.contrib import admin
from django.utils.html import format_html
from .models import ElementType, Element


@admin.register(ElementType)
class ElementTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'world', 'icon', 'color', 'elements_count', 'created_at']
    list_filter = ['world', 'created_at']
    search_fields = ['name', 'world__name']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'world', 'icon', 'color')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def elements_count(self, obj):
        return obj.elements.count()

    elements_count.short_description = 'Количество элементов'


@admin.register(Element)
class ElementAdmin(admin.ModelAdmin):
    list_display = ['name', 'element_type', 'world', 'created_at', 'updated_at', 'preview_fields']
    list_filter = ['world', 'element_type', 'created_at']
    search_fields = ['name', 'element_type__name', 'world__name']
    readonly_fields = ['created_at', 'updated_at', 'formatted_data', 'formatted_schema']

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'world', 'element_type')
        }),
        ('Схема полей (JSON)', {
            'fields': ('formatted_schema',),
            'description': 'Структура полей элемента (типы, названия)'
        }),
        ('Данные элемента (JSON)', {
            'fields': ('formatted_data',),
            'description': 'Значения полей элемента'
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def preview_fields(self, obj):
        """Превью полей в списке"""
        if obj.data:
            items = []
            for key, value in list(obj.data.items())[:3]:
                if key != '_cover':
                    if isinstance(value, dict):
                        caption = value.get('caption', '')
                        items.append(f"{key}: {caption[:20]}")
                    elif isinstance(value, list):
                        items.append(f"{key}: [{len(value)}]")
                    else:
                        items.append(f"{key}: {str(value)[:30]}")

            if items:
                # Используем mark_safe вместо format_html без аргументов
                from django.utils.safestring import mark_safe
                return mark_safe('<br>'.join(items))
            return '—'
        return '—'

    preview_fields.short_description = 'Поля (превью)'

    def formatted_data(self, obj):
        """Красивое отображение JSON данных"""
        import json
        if obj.data:
            json_str = json.dumps(obj.data, indent=2, ensure_ascii=False)
            return format_html(
                '<pre style="background: #1e1e2e; color: #cdd6f4; padding: 15px; border-radius: 8px; '
                'max-height: 400px; overflow: auto; font-family: monospace; font-size: 13px;">{}</pre>',
                json_str
            )
        return 'Нет данных'

    formatted_data.short_description = 'Данные'

    def formatted_schema(self, obj):
        """Красивое отображение JSON схемы"""
        import json
        if obj.fields_schema:
            json_str = json.dumps(obj.fields_schema, indent=2, ensure_ascii=False)
            return format_html(
                '<pre style="background: #1e1e2e; color: #cdd6f4; padding: 15px; border-radius: 8px; '
                'max-height: 400px; overflow: auto; font-family: monospace; font-size: 13px;">{}</pre>',
                json_str
            )
        return 'Нет схемы'

    formatted_schema.short_description = 'Схема полей'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "world":
            kwargs["required"] = False
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if obj.element_type and not obj.world:
            obj.world = obj.element_type.world
        super().save_model(request, obj, form, change)