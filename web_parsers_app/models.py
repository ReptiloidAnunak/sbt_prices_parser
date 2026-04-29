from django.db import models


PARSER_CHOICES = [
    ("duna", "Duna"),
    ("electrocity", "Electrocity"),
    ("electrofrig", "Electrofrig"),
    ("fijamom", "Fijamom"),
    ("nordfrig", "Nordfrig"),
    ("roma", "Roma"),
    ("ansal", "Ansal"),
    ("reld_retail", "Reld retail"),
    ("bellini_retail", "Bellini retail"),
    ("refrigeracion_norte_retail", "Refrigeracion Norte retail"),
]


class ParserJob(models.Model):
    class Meta:
        verbose_name = "Веб-парсер"
        verbose_name_plural = "Веб-парсеры"
        ordering = ["name"]

    name = models.CharField(
        max_length=100,
        unique=True,
        choices=PARSER_CHOICES,
        verbose_name="Код парсера",
    )
    title = models.CharField(
        max_length=255,
        verbose_name="Название",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен",
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
        default="",
        verbose_name="Статус",
    )
    last_result = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Результат",
    )
    last_error = models.TextField(
        blank=True,
        default="",
        verbose_name="Ошибка",
    )

    def __str__(self):
        return self.title

    @classmethod
    def load_default_parsers(cls):
        for name, title in PARSER_CHOICES:
            cls.objects.get_or_create(
                name=name,
                defaults={
                    "title": title,
                    "is_active": True,
                },
            )