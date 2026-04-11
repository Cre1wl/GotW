from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Получить значение из словаря по ключу"""
    if dictionary is None:
        return None
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None


@register.filter
def get_cover(data):
    """Получить первое изображение из данных элемента для обложки"""
    if not data:
        return None

    if isinstance(data, dict):
        # Сначала проверяем специальное поле _cover
        if data.get('_cover'):
            return data.get('_cover')

        # Затем ищем любое изображение
        for key, value in data.items():
            if isinstance(value, str):
                if value.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp')):
                    return value
                if '/media/' in value and any(
                        ext in value.lower() for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
                    return value

    return None