import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from django.conf import settings

CREDENTIALS_FILE = r'D:\3 course\6 sem\ISIS\key\credentials.json'

SPREADSHEET_ID = '1TzChVZLZG8_BLMyeZsom_j0wi8YPSvDHIFX9p1i45jQ'

def get_sheets_service():
    """Подключение к Google Sheets API"""
    if not os.path.exists(CREDENTIALS_FILE):
        raise FileNotFoundError(f"Файл {CREDENTIALS_FILE} не найден!")

    creds = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    return build('sheets', 'v4', credentials=creds)


def export_worlds_to_sheets():
    """Экспорт миров в Google Sheets"""
    from worlds.models import World

    service = get_sheets_service()
    sheet = service.spreadsheets()

    worlds = World.objects.all()

    headers = ['ID', 'Название', 'Описание', 'Создатель', 'Дата создания']
    rows = []
    for w in worlds:
        rows.append([
            str(w.id),
            w.name,
            w.description or '',
            w.creator.username if w.creator else '',
            w.created_at.strftime('%Y-%m-%d %H:%M')
        ])

    data = [headers] + rows

    body = {'values': data}
    sheet.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range='Миры!A1',
        valueInputOption='RAW',
        body=body
    ).execute()

    return len(worlds)


def export_elements_to_sheets():
    """Экспорт элементов в Google Sheets"""
    from elements.models import Element

    service = get_sheets_service()
    sheet = service.spreadsheets()

    elements = Element.objects.all()

    headers = ['ID', 'Название', 'Тип', 'Мир', 'Данные (JSON)', 'Дата создания']
    rows = []
    for e in elements:
        data_json = json.dumps(e.data, ensure_ascii=False)
        if len(data_json) > 500:
            data_json = data_json[:500] + '...'
        rows.append([
            str(e.id),
            e.name,
            e.element_type.name if e.element_type else '-',
            e.world.name if e.world else '-',
            data_json,
            e.created_at.strftime('%Y-%m-%d %H:%M')
        ])

    data = [headers] + rows

    body = {'values': data}
    sheet.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range='Элементы!A1',
        valueInputOption='RAW',
        body=body
    ).execute()

    return len(elements)


def sync_all_to_sheets():
    """Синхронизация всех данных"""
    worlds_count = export_worlds_to_sheets()
    elements_count = export_elements_to_sheets()

    return {
        'worlds': worlds_count,
        'elements': elements_count,
        'message': f'Синхронизировано миров: {worlds_count}, элементов: {elements_count}'
    }