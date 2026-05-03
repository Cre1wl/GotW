import requests
import logging
import json
from django.conf import settings

logger = logging.getLogger(__name__)


def create_crm_contact(element):
    """
    Отправляет данные элемента в Битрикс24 для создания контакта.
    Возвращает ID созданного контакта или None при ошибке.
    """
    webhook_url = getattr(settings, 'BITRIX24_WEBHOOK_URL', None)
    if not webhook_url:
        logger.warning("BITRIX24_WEBHOOK_URL не задан. Интеграция пропущена.")
        return None

    # 1. Базовые поля
    contact_name = element.name               # имя персонажа
    world_name = element.world.name           # мир
    category_name = element.element_type.name # тип (Персонаж, Локация…)

    # 2. Обложка (хранится в data['_cover'])
    cover_url = ''
    if isinstance(element.data, dict):
        cover_url = element.data.get('_cover', '')
    elif isinstance(element.data, str):
        try:
            data_dict = json.loads(element.data)
            cover_url = data_dict.get('_cover', '')
        except:
            pass

    # 3. Описание — берём из data, если там есть ключ "description",
    #    иначе можно оставить пустым или взять из специального поля.
    description = ''
    if isinstance(element.data, dict):
        description = element.data.get('description', '')
    elif isinstance(element.data, str):
        try:
            data_dict = json.loads(element.data)
            description = data_dict.get('description', '')
        except:
            pass

    # 4. Дополнительные поля – собираем все кастомные атрибуты в JSON-строку
    extra_fields = {}
    fields_schema = element.fields_schema or {}
    element_data = element.data or {}

    # Приводим data к словарю, если это строка
    if isinstance(element_data, str):
        try:
            element_data = json.loads(element_data)
        except:
            element_data = {}

    for field_key, field_def in fields_schema.items():
        if field_key == '_cover' or field_key == 'description':
            continue  # уже обработали отдельно
        field_name = field_def.get('name', field_key)
        value = element_data.get(field_key)
        if value is not None:
            # Для списков (tags, multiselect) превращаем в строку через запятую
            if isinstance(value, list):
                value = ', '.join(str(v) for v in value)
            extra_fields[field_name] = value

    extra_fields_str = json.dumps(extra_fields, ensure_ascii=False)

    # 5. Формируем запрос к API (коды полей замените на свои реальные UF_CRM_...)
    fields = {
        "NAME": contact_name,                       # системное имя контакта
        "UF_CRM_1777801083": world_name,            # Мир
        "UF_CRM_1777803542089": element.name,  # Имя объекта
        "UF_CRM_1777801127": category_name,         # Тип
        "UF_CRM_1777801166": cover_url,             # Обложка (ссылка)
        "UF_CRM_1777801198": description,           # Описание
        "UF_CRM_1777801518": extra_fields_str,      # Дополнительные поля (JSON)
        "COMMENTS": f"Создано из GotW. ID элемента: {element.id}",
    }

    api_url = f"{webhook_url.rstrip('/')}/crm.contact.add.json"

    try:
        response = requests.post(api_url, json={"fields": fields}, timeout=15)
        response.raise_for_status()
        data = response.json()
        if "result" in data:
            contact_id = data["result"]
            logger.info(f"Контакт создан в CRM. ID: {contact_id}")
            return contact_id
        else:
            logger.error(f"Ошибка API: {data}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка сети или запроса: {e}")
        return None