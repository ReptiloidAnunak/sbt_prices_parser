from django.contrib import admin, messages
from django.utils.html import format_html

from .models import Product, ProductSupplier
from supplier.models import Supplier
from .forms import SupplierAdminForm


class ProductSupplierInline(admin.TabularInline):
    model = ProductSupplier
    extra = 0
    autocomplete_fields = ["supplier"]
    fields = (
        "supplier",
        "supplier_prod_code",
        "supplier_prod_title",
        "product_price_sbt",
        "price_wholesale",
        "price_wholesale_final",
        "price_retail",
        "supplier_iva_in_price",
        "supplier_discount_percent",
        "updated_at",
    )
    readonly_fields = (
        "product_price_sbt",
        "updated_at",
        "supplier_iva_in_price",
        "supplier_discount_percent",
    )

    def product_price_sbt(self, obj):
        if not obj or not obj.product_id:
            return "-"
        return obj.product.price_sbt
    product_price_sbt.short_description = "Цена СБТ"

    def supplier_iva_in_price(self, obj):
        if not obj or not obj.supplier_id:
            return None
        return obj.supplier.iva_in_price
    supplier_iva_in_price.short_description = "IVA в цене"
    supplier_iva_in_price.boolean = True

    def supplier_discount_percent(self, obj):
        if not obj or not obj.supplier_id or obj.supplier.discount is None:
            return "-"
        return f"{obj.supplier.discount * 100:g}"
    supplier_discount_percent.short_description = "Скидка %"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "code_sbt",
        "title_sbt",
        "category",
        "price_sbt",
        "best_price_wholesale",
        "best_price_retail",
    )

    list_filter = (
        "category",
    )

    search_fields = (
        "title_sbt",
    )

    ordering = (
        "title_sbt",
    )

    inlines = [ProductSupplierInline]


@admin.register(ProductSupplier)
class ProductSupplierAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "product_price_sbt",
        "supplier",
        "price_wholesale",
        "price_wholesale_final",
        "price_retail",
        "supplier_iva_in_price",
        "supplier_discount_percent",
        "updated_at",
    )

    list_filter = (
        "supplier",
    )

    search_fields = (
        "product__title_sbt",
        "supplier__name",
        "supplier_prod_code",
    )

    autocomplete_fields = (
        "product",
        "supplier",
    )

    def product_price_sbt(self, obj):
        if not obj or not obj.product_id:
            return "-"
        return obj.product.price_sbt
    product_price_sbt.short_description = "Цена СБТ"

    def supplier_iva_in_price(self, obj):
        if not obj or not obj.supplier_id:
            return None
        return obj.supplier.iva_in_price
    supplier_iva_in_price.short_description = "IVA в цене"
    supplier_iva_in_price.boolean = True

    def supplier_discount_percent(self, obj):
        if not obj or not obj.supplier_id or obj.supplier.discount is None:
            return "-"
        return f"{obj.supplier.discount * 100:g}"
    supplier_discount_percent.short_description = "Скидка %"


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    form = SupplierAdminForm

    list_display = (
        "name",
        "website",
        "contact_email",
        "whatsapp",
        "price_list_link",
        "iva_in_price",
        "discount_percent",
        "upt_price_at",
    )

    search_fields = ("name",)

    def price_list_link(self, obj):
        if obj.price_list:
            url = obj.price_list.url
            request = getattr(self, "_request", None)

            if request:
                url = request.build_absolute_uri(url)

            return format_html(
                '<a href="{}" target="_blank">Скачать</a>',
                url
            )
        return "-"
    price_list_link.short_description = "Прайс"

    def discount_percent(self, obj):
        if obj.discount is None:
            return "-"
        return f"{obj.discount * 100:g}"
    discount_percent.short_description = "Скидка %"

    def save_model(self, request, obj, form, change):
        if obj.website and str(obj.website).lower() == "nan":
            obj.website = None

        super().save_model(request, obj, form, change)

        if obj.price_list:
            self.message_user(
                request,
                "Файл загружен и отправлен в обработку 🚀",
                level=messages.SUCCESS
            )