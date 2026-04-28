from django.apps import AppConfig


class WebParsersAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "web_parsers_app"
    verbose_name = "Парсеры"

    def ready(self):
        # Автоматически создаём строки парсеров в админке.
        # try/except нужен, чтобы не валить migrate/start, когда БД ещё не готова.
        try:
            from .models import ParserJob
            ParserJob.load_default_parsers()
        except Exception:
            pass