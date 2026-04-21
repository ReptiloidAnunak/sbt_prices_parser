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
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['title_sbt']

    category = models.CharField(
        max_length=255,
        choices=CATEGORY_CHOICES,
        verbose_name="Категория"
    )

    code_sbt = models.IntegerField(null=True, blank=True, verbose_name="Код СБТ")
    title_sbt = models.CharField(max_length=255, verbose_name="Название СБТ", unique=True)
    price_sbt = models.IntegerField(verbose_name="Цена СБТ", null=True, blank=True)

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

    supplier_prod_code = models.CharField(max_length=255, verbose_name="Код тов. поставщика")
    supplier_prod_title = models.CharField(max_length=255, verbose_name="Название тов. поставщика")

    price_wholesale = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Оптовая цена из прайса"
    )

    price_wholesale_final = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Оптовая цена"
    )

    iva_in_price = models.BooleanField(default=False)

    price_retail = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Розничная цена"
    )

    updated_at = models.DateTimeField(auto_now=True, verbose_name='Время обновления')

    def calculate_price_wholesale_final(self):
        if self.price_wholesale is None:
            return None

        price = Decimal(str(self.price_wholesale))

        # 1. Если IVA не включён в цену поставщика — добавляем 21%
        if self.supplier and not self.supplier.iva_in_price:
            price = price * Decimal("1.21")

        # 2. Если есть скидка поставщика — вычитаем её
        if self.supplier and self.supplier.discount is not None:
            discount = Decimal(str(self.supplier.discount))

            # если в базе хранится 0.25 для 25%
            multiplier = Decimal("1.00") - discount

            if multiplier < 0:
                multiplier = Decimal("0.00")

            price = price * multiplier

        return price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def save(self, *args, **kwargs):
        self.price_wholesale_final = self.calculate_price_wholesale_final()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product} - {self.supplier} (W:{self.price_wholesale_final} R:{self.price_retail})"