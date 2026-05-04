from django.db import models
from django.utils import timezone


class ParserJob(models.Model):
    PARSER_CHOICES = [
        ("duna", "Duna"),
        ("electrocity", "Electrocity"),
        ("electrofrig", "Electrofrig"),
        ("fijamom", "Fijamom"),
        ("nordfrig", "Nordfrig"),
        ("roma", "Roma"),
        ("ansal", "Ansal"),
        ("ansal_retail", "Ansal retail"),
        ("reld_retail", "Reld retail"),
        ("bellini_retail", "Bellini retail"),
        ("refrigeracion_norte_retail", "Refrigeracion Norte retail"),
    ]

    name = models.CharField(
        max_length=100,
        choices=PARSER_CHOICES,
        unique=True,
        verbose_name="Парсер",
    )

    last_run_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Последний запуск",
    )

    last_success_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Последний успешный запуск",
    )

    last_status = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Статус",
    )

    last_result = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Результат",
    )

    last_error = models.TextField(
        blank=True,
        verbose_name="Ошибка",
    )

    def __str__(self):
        return self.name

    # 🔥 ВАЖНО: фикс логов
    @property
    def log_name(self):
        if self.name == "ansal_retail":
            return "ansal"
        return self.name

    # 🔧 загрузка дефолтных парсеров
    @classmethod
    def load_default_parsers(cls):
        for parser_key, parser_label in cls.PARSER_CHOICES:
            cls.objects.get_or_create(name=parser_key)

    class Meta:
        verbose_name = "Парсер"
        verbose_name_plural = "Парсеры"
        ordering = ["name"]