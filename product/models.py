import json
from decimal import Decimal, ROUND_HALF_UP
from django.db import models
from supplier.models import Supplier
from api_server.settings import CATEGORIES_FILE


with open(CATEGORIES_FILE, encoding="utf-8") as f:
    categories = json.load(f)

CATEGORY_CHOICES = [(c, c) for c in categories]


class Product(models.Model):

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ["title_sbt"]

    category = models.CharField(
        max_length=255,
        choices=CATEGORY_CHOICES,
        verbose_name="Категория"
    )

    code_sbt = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Код СБТ"
    )

    title_sbt = models.CharField(
        max_length=255,
        unique=True,
        verbose_name="Название СБТ"
    )

    price_sbt = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Цена СБТ"
    )

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
        price = self.product_suppliers.order_by("price_wholesale_final").first()
        return price.price_wholesale_final if price else None

    def best_price_retail(self):
        price = self.product_suppliers.order_by("price_retail").first()
        return price.price_retail if price else None


class ProductSupplier(models.Model):

    class Meta:
        verbose_name = "Цена поставщика"
        verbose_name_plural = "Цены поставщиков"
        unique_together = ("product", "supplier")
        ordering = ["price_wholesale_final"]

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

    supplier_prod_code = models.CharField(
        max_length=255,
        verbose_name="Код тов. поставщика"
    )

    supplier_prod_title = models.CharField(
        max_length=255,
        verbose_name="Название тов. поставщика"
    )

    price_wholesale = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Оптовая ориг. цена из прайса"
    )

    price_wholesale_final = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Оптовая финальная цена"
    )

    price_retail = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Розничная цена"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Время обновления"
    )

    def calculate_price_wholesale_final(self):
        if self.price_wholesale is None:
            return None

        base_price = Decimal(str(self.price_wholesale))
        price = base_price

        if self.supplier:
            if not self.supplier.iva_in_price:
                price += base_price * Decimal("0.21")

            if not self.supplier.ib_caba_in_prise:
                price += base_price * Decimal("0.03")

            if self.supplier.discount is not None:
                discount = Decimal(str(self.supplier.discount))

                if discount < Decimal("0"):
                    discount = Decimal("0")
                elif discount > Decimal("100"):
                    discount = Decimal("100")

                price -= price * (discount / Decimal("100"))

        return price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def save(self, *args, **kwargs):
        self.price_wholesale_final = self.calculate_price_wholesale_final()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product} - {self.supplier} (W:{self.price_wholesale_final} R:{self.price_retail})"