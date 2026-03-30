import os
import re
from django.db import models


def supplier_price_upload_path(instance, filename):
    ext = filename.split('.')[-1]  # получаем расширение файла
    supplier_name = re.sub(r'[^a-zA-Z0-9_-]', '_', instance.name)

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
    whatsapp = models.CharField(max_length=200,blank=True,  null=True)
    facebook = models.URLField(max_length=200, blank=True, null=True)
    login = models.CharField(max_length=200,blank=True,  null=True)
    password = models.CharField(max_length=200,blank=True,  null=True)
    price_list = models.FileField(
        upload_to=supplier_price_upload_path,
        null=True,
        blank=True
    )

    def __str__(self):
        return self.name