from django.contrib import admin
from .models import Product, ProductSupplier
from supplier.models import Supplier


class ProductSupplierInline(admin.TabularInline):
    model = ProductSupplier
    extra = 0
    autocomplete_fields = ["supplier"]
    fields = (
        "supplier",
        "supplier_prod_code",
        "supplier_prod_title",
        "price_wholesale",
        "price_retail",
        "updated_at",
    )
    readonly_fields = ("updated_at",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = (
        "title_sbt",
        "category",
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
        "supplier",
        "price_wholesale",
        "price_retail",
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


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "website",
        "contact_email",
        "whatsapp",
    )

    search_fields = (
        "name",
    )