import os
import re
import datetime
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


def supplier_price_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    supplier_name = re.sub(r'[^a-zA-Z0-9_-]', '_', instance.name).lower()
    instance.updated_at = datetime.datetime.now()
    new_filename = f"{supplier_name}.{ext}"
    return os.path.join("price_lists", new_filename)


class Supplier(models.Model):
    class Meta:
        verbose_name = 'Поставщик'
        verbose_name_plural = 'Поставщики'
        ordering = ['name']

    name = models.CharField(max_length=255, unique=True)
    website = models.URLField(blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    whatsapp = models.CharField(max_length=200, blank=True, null=True)
    facebook = models.URLField(max_length=200, blank=True, null=True)
    login = models.CharField(max_length=200, blank=True, null=True)
    password = models.CharField(max_length=200, blank=True, null=True)
    price_list = models.FileField(
        upload_to=supplier_price_upload_path,
        null=True,
        blank=True
    )
    updated_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.name

    def process_price_list_async(self):
        """Запускаем Celery задачу вручную"""
        if self.price_list:
            from supplier.tasks import process_price_list
            process_price_list.delay(self.id)



@receiver(post_save, sender=Supplier)
def trigger_price_list_parse(sender, instance, created, **kwargs):
    """
    Автоматически запускаем Celery задачу при загрузке/обновлении прайс-листа
    """
    if instance.price_list:
        from supplier.tasks import process_price_list
        process_price_list.delay(instance.id)