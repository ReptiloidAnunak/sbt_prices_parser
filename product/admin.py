from django.contrib import admin, messages
from .models import Product, ProductSupplier
from supplier.models import Supplier
from .forms import SupplierAdminForm 
from django.utils.html import format_html

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
    form = SupplierAdminForm

    list_display = (
        "name",
        "website",
        "contact_email",
        "whatsapp",
        "price_list_link",
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

    def save_model(self, request, obj, form, change):
        if obj.website and str(obj.website).lower() == 'nan':
            obj.website = None

        super().save_model(request, obj, form, change)

        if obj.price_list:
            # process_price_list.delay(obj.id)  # 🔥 запуск Celery

            self.message_user(
                request,
                "Файл загружен и отправлен в обработку 🚀",
                level=messages.SUCCESS
            )