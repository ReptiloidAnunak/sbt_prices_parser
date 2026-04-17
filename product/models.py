import json
from django.db import models
from supplier.models import Supplier
from api_server.settings import CATEGORIES_FILE


with open(CATEGORIES_FILE, encoding="utf-8") as f:
    categories = json.load(f)

CATEGORY_CHOICES = [(c, c) for c in categories]


class Product(models.Model):

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['title_sbt']

    category = models.CharField(
        max_length=255,
        choices=CATEGORY_CHOICES,
        verbose_name="Категория"
    )

    code_sbt = models.IntegerField(null=True, verbose_name="Код СБТ")

    title_sbt = models.CharField(max_length=255, verbose_name="Название СБТ")

    suppliers = models.ManyToManyField(
        Supplier,
        through="ProductSupplier",
        related_name="products",
        blank=True,
        verbose_name="Поставщик"
    )

    def __str__(self):
        return self.title_sbt

    def best_price_wholesale(self):
        price = self.product_suppliers.order_by("price_wholesale").first()
        return price.price_wholesale if price else None

    def best_price_retail(self):
        price = self.product_suppliers.order_by("price_retail").first()
        return price.price_retail if price else None


class ProductSupplier(models.Model):

    class Meta:
        verbose_name = "Цена поставщика"
        verbose_name_plural = "Цены поставщиков"
        unique_together = ("product", "supplier")
        ordering = ["price_wholesale"]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="product_suppliers",
        verbose_name="Товар"
    )

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name="supplier_products",
        verbose_name="Поставщик"
    )
    
    supplier_prod_code = models.CharField(max_length=255, verbose_name="Код тов. поставщика")
    supplier_prod_title = models.CharField(max_length=255, verbose_name="Название тов. поставщика")

    price_wholesale = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Оптовая цена"
    )

    price_with_iva = models.BooleanField(
        default=False
    )

    price_retail = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Розничная цена"
    )

    updated_at = models.DateTimeField(auto_now=True, verbose_name='Время обновления')

    def __str__(self):
        return f"{self.product} - {self.supplier} (W:{self.price_wholesale} R:{self.price_retail})"