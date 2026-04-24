import os
import re
from django.db import models
from django.core.files.storage import FileSystemStorage

from product.models import Product


class OverwriteStorage(FileSystemStorage):
    def get_available_name(self, name, max_length=None):
        if self.exists(name):
            os.remove(os.path.join(self.location, name))
        return name


def mercadolibre_price_upload_path(instance, filename):
    ext = filename.split(".")[-1]
    shop_name = re.sub(r"[^a-zA-Z0-9_-]", "_", instance.name).lower()
    new_filename = f"{shop_name}.{ext}"
    return os.path.join("mercadolibre_price_lists", new_filename)


class MercadoLibreShop(models.Model):
    class Meta:
        verbose_name = "Магазин Mercado Libre"
        verbose_name_plural = "Магазины Mercado Libre"
        ordering = ["name"]

    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name="Название"
    )
    ml_page = models.URLField(
        blank=True,
        null=True,
        verbose_name="Ссылка Mercado Libre"
    )
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
    price_list = models.FileField(
        upload_to=mercadolibre_price_upload_path,
        storage=OverwriteStorage(),
        null=True,
        blank=True,
        verbose_name="Прайс"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Время обновления"
    )

    def __str__(self):
        return self.name


class MercadoLibreProduct(models.Model):
    class Meta:
        verbose_name = "Товар Mercado Libre"
        verbose_name_plural = "Товары Mercado Libre"
        unique_together = ("product", "shop")
        ordering = ["price"]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="mercadolibre_products",
        verbose_name="Товар"
    )

    shop = models.ForeignKey(
        MercadoLibreShop,
        on_delete=models.CASCADE,
        related_name="mercadolibre_products",
        verbose_name="Магазин Mercado Libre"
    )

    shop_prod_code = models.CharField(
        max_length=255,
        verbose_name="Код товара магазина"
    )
    shop_prod_title = models.CharField(
        max_length=255,
        verbose_name="Название товара магазина"
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Цена из прайса"
    )


    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Время обновления"
    )

    def __str__(self):
        return f"{self.product} - {self.shop} (W:{self.price_wholesale_final} R:{self.price_retail})"