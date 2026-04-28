from django.contrib import admin, messages
from django.utils.html import format_html

from .models import Product, ProductSupplier
from supplier.models import Supplier
from .forms import SupplierAdminForm
from mercado_libre.models import MercadoLibreProduct, MercadoLibreShop


from django.contrib import admin
from options.models import Options
from django.contrib import admin, messages
from django.http import FileResponse, Http404
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html
from django.conf import settings

from web_parsers_app.models import ParserJob
from web_parsers_app.tasks import run_web_parser, run_ansal_parser

@admin.register(Options)
class OptionsAdmin(admin.ModelAdmin):

    def has_add_permission(self, request):
        # нельзя создавать больше одного
        return not Options.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # нельзя удалять
        return False


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
        "supplier_ib_caba_in_price",
        "supplier_discount_percent",
        "updated_at",
    )
    readonly_fields = (
        "product_price_sbt",
        "updated_at",
        "supplier_iva_in_price",
        "supplier_ib_caba_in_price",
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

    def supplier_ib_caba_in_price(self, obj):
        if not obj or not obj.supplier_id:
            return None
        return obj.supplier.ib_caba_in_prise
    supplier_ib_caba_in_price.short_description = "IB CABA"
    supplier_ib_caba_in_price.boolean = True

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
        "supplier_ib_caba_in_price",
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

    def supplier_ib_caba_in_price(self, obj):
        if not obj or not obj.supplier_id:
            return None
        return obj.supplier.ib_caba_in_prise
    supplier_ib_caba_in_price.short_description = "IB CABA"
    supplier_ib_caba_in_price.boolean = True

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
        "ib_caba_in_prise",
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


@admin.register(MercadoLibreShop)
class MercadoLibreShopAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "ml_page",
        "contact_email",
        "whatsapp",
        "updated_at",
    )
    search_fields = ("name", "contact_email", "whatsapp")
    list_filter = ("updated_at",)
    readonly_fields = ("updated_at",)

    fieldsets = (
        ("Основная информация", {
            "fields": ("name", "ml_page")
        }),
        ("Контакты", {
            "fields": ("contact_email", "whatsapp", "facebook")
        }),
        ("Файлы", {
            "fields": ("price_list",)
        }),
        ("Системные", {
            "fields": ("updated_at",)
        }),
    )


class MercadoLibreProductInline(admin.TabularInline):
    model = MercadoLibreProduct
    extra = 0
    autocomplete_fields = ("product",)
    fields = (
        "product",
        "shop_prod_code",
        "shop_prod_title",
        "price",
        "updated_at",
    )
    readonly_fields = ("updated_at",)


@admin.register(MercadoLibreProduct)
class MercadoLibreProductAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "shop",
        "shop_prod_code",
        "price",
        "updated_at",
    )
    list_filter = ("shop", "updated_at")
    search_fields = (
        "product__name",
        "shop__name",
        "shop_prod_code",
        "shop_prod_title",
    )
    autocomplete_fields = ("product", "shop")
    readonly_fields = ("updated_at",)

    fieldsets = (
        ("Связи", {
            "fields": ("product", "shop")
        }),
        ("Данные магазина", {
            "fields": ("shop_prod_code", "shop_prod_title", "price")
        }),
        ("Системные", {
            "fields": ("updated_at",)
        }),
    )


@admin.register(ParserJob)
class ParserJobAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "title",
        "is_active",
        "last_status",
        "last_run_at",
        "last_success_at",
        "run_button",
        "log_link",
    )
    list_filter = ("is_active", "last_status")
    search_fields = ("name", "title")
    readonly_fields = (
        "last_run_at",
        "last_success_at",
        "last_status",
        "last_result",
        "last_error",
    )

    def get_urls(self):
        custom_urls = [
            path(
                "run-parser/<int:parser_id>/",
                self.admin_site.admin_view(self.run_parser),
                name="web_parsers_app_parserjob_run_parser",
            ),
            path(
                "log/<int:parser_id>/",
                self.admin_site.admin_view(self.view_log),
                name="web_parsers_app_parserjob_log",
            ),
        ]
        return custom_urls + super().get_urls()

    def run_button(self, obj):
        if not obj.is_active:
            return "Отключен"

        url = reverse(
            "admin:web_parsers_app_parserjob_run_parser",
            args=[obj.pk],
        )
        return format_html('<a class="button" href="{}">Запустить</a>', url)
    run_button.short_description = "Запуск"

    def log_link(self, obj):
        url = reverse(
            "admin:web_parsers_app_parserjob_log",
            args=[obj.pk],
        )
        return format_html('<a class="button" href="{}" target="_blank">Лог</a>', url)
    log_link.short_description = "Лог"

    def run_parser(self, request, parser_id):
        parser = ParserJob.objects.get(pk=parser_id)
        changelist_url = reverse("admin:web_parsers_app_parserjob_changelist")

        if not parser.is_active:
            self.message_user(request, f"{parser.title} отключен", level=messages.WARNING)
            return redirect(changelist_url)

        parser.last_run_at = timezone.now()
        parser.last_status = "RUNNING"
        parser.last_error = ""
        parser.save(update_fields=["last_run_at", "last_status", "last_error"])

        try:
            if parser.name == "ansal":
                run_ansal_parser.delay()
            else:
                run_web_parser.delay(parser.name)

            self.message_user(request, f"{parser.title} запущен 🚀", level=messages.SUCCESS)
        except Exception as e:
            parser.last_status = "ERROR"
            parser.last_error = str(e)
            parser.save(update_fields=["last_status", "last_error"])
            self.message_user(request, f"Ошибка запуска {parser.title}: {e}", level=messages.ERROR)

        return redirect(changelist_url)

    def view_log(self, request, parser_id):
        parser = ParserJob.objects.get(pk=parser_id)
        log_path = settings.BASE_DIR / "logs" / "parsers" / f"{parser.name}.log"

        if not log_path.exists():
            raise Http404("Log file not found")

        return FileResponse(
            open(log_path, "rb"),
            content_type="text/plain; charset=utf-8",
            as_attachment=False,
            filename=f"{parser.name}.log",
        )