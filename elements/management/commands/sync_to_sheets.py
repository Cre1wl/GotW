from django.core.management.base import BaseCommand
from gotw.gsheets_export import sync_all_to_sheets


class Command(BaseCommand):
    help = 'Синхронизация данных с Google Sheets'

    def handle(self, *args, **options):
        try:
            result = sync_all_to_sheets()
            self.stdout.write(
                self.style.SUCCESS(f'✅ {result["message"]}')
            )
        except FileNotFoundError as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка: {e}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка: {e}')
            )