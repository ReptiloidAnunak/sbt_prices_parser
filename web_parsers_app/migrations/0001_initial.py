# Generated manually for ParserJob

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ParserJob",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(choices=[("duna", "Duna"), ("electrocity", "Electrocity"), ("electrofrig", "Electrofrig"), ("fijamom", "Fijamom"), ("nordfrig", "Nordfrig"), ("roma", "Roma"), ("ansal", "Ansal")], max_length=100, unique=True, verbose_name="Код парсера")),
                ("title", models.CharField(max_length=255, verbose_name="Название")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активен")),
                ("last_run_at", models.DateTimeField(blank=True, null=True, verbose_name="Последний запуск")),
                ("last_success_at", models.DateTimeField(blank=True, null=True, verbose_name="Последний успешный запуск")),
                ("last_status", models.CharField(blank=True, default="", max_length=50, verbose_name="Статус")),
                ("last_result", models.JSONField(blank=True, null=True, verbose_name="Результат")),
                ("last_error", models.TextField(blank=True, default="", verbose_name="Ошибка")),
            ],
            options={
                "verbose_name": "Веб-парсер",
                "verbose_name_plural": "Веб-парсеры",
                "ordering": ["name"],
            },
        ),
    ]