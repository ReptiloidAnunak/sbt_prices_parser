import os
import re
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.files.storage import FileSystemStorage
from django.utils import timezone


# --- Валюта (правильный Django способ)
class CurrencyChoices(models.TextChoices):
    USD = "USD", "USD"
    ARS = "ARS", "ARS"


class DataType(models.TextChoices):
    doc = 'doc', 'doc'
    web = 'web', 'web'
    doc_web = 'doc, web'

# --- Перезапись файла
class OverwriteStorage(FileSystemStorage):
    def get_available_name(self, name, max_length=None):
        if self.exists(name):
            os.remove(os.path.join(self.location, name))
        return name


# --- Путь загрузки прайса
def supplier_price_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    supplier_name = re.sub(r'[^a-zA-Z0-9_-]', '_', instance.name).lower()

    instance.upt_price_at = timezone.now()

    new_filename = f"{supplier_name}.{ext}"
    return os.path.join("price_lists", new_filename)


class Supplier(models.Model):

    class Meta:
        verbose_name = 'Поставщик'
        verbose_name_plural = 'Поставщики'
        ordering = ['name']

    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name="Название"
    )

    website = models.URLField(
        blank=True,
        null=True,
        verbose_name="Сайт"
    )

    data_type = models.CharField(choices=DataType, verbose_name="Тип данных", null=True, blank=True)

    contact_email = models.EmailField(
        blank=True,
        null=True,
        verbose_name="Почта"
    )

    whatsapp = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Whatsapp"
    )

    facebook = models.URLField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Facebook"
    )

    login = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Логин"
    )

    password = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Пароль"
    )

    iva_in_price = models.BooleanField(
        default=False,
        verbose_name="IVA включен в цену"
    )

    ib_caba_in_prise = models.BooleanField(
        default=False,
        verbose_name="IB CABA включен в цену"
    )

    discount = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Скидка %"
    )

    # --- ВАЛЮТА
    currency = models.CharField(
        max_length=3,
        choices=CurrencyChoices.choices,
        default=CurrencyChoices.ARS,
        verbose_name="Валюта"
    )

    price_list = models.FileField(
        upload_to=supplier_price_upload_path,
        storage=OverwriteStorage(),
        null=True,
        blank=True,
        verbose_name="Прайс"
    )

    upt_price_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Обновление прайса"
    )

    def __str__(self):
        return self.name

    def process_price_list_async(self):
        """Запускаем Celery задачу вручную"""
        if self.price_list:
            from supplier.tasks import process_price_list
            process_price_list.delay(self.id)


# --- Автоматический запуск парсинга
@receiver(post_save, sender=Supplier)
def trigger_price_list_parse(sender, instance, created, **kwargs):
    if instance.price_list:
        from supplier.tasks import process_price_list
        process_price_list.delay(instance.id)