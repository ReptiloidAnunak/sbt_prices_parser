from django.contrib import admin, messages
from django.utils.html import format_html
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils import timezone
from django.conf import settings

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from openpyxl.utils import get_column_letter

from .models import Product, ProductSupplier
from supplier.models import Supplier
from .forms import SupplierAdminForm
from mercado_libre.models import MercadoLibreProduct, MercadoLibreShop

from options.models import Options

from web_parsers_app.models import ParserJob
from web_parsers_app.tasks import run_web_parser, run_ansal_parser


@admin.register(Options)
class OptionsAdmin(admin.ModelAdmin):

    def has_add_permission(self, request):
        return not Options.objects.exists()

    def has_delete_permission(self, request, obj=None):
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
        return obj.product.price_sbt if obj.product_id else "-"
    product_price_sbt.short_description = "Цена СБТ"

    def supplier_iva_in_price(self, obj):
        return obj.supplier.iva_in_price if obj.supplier_id else None
    supplier_iva_in_price.boolean = True

    def supplier_ib_caba_in_price(self, obj):
        return obj.supplier.ib_caba_in_prise if obj.supplier_id else None
    supplier_ib_caba_in_price.boolean = True

    def supplier_discount_percent(self, obj):
        return f"{obj.supplier.discount * 100:g}" if obj.supplier and obj.supplier.discount else "-"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "code_sbt",
        "title_sbt",
        "category",
        "price_sbt",
    )

    search_fields = ("title_sbt",)
    ordering = ("title_sbt",)
    inlines = [ProductSupplierInline]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "export-supplier-matrix/",
                self.admin_site.admin_view(self.export_supplier_matrix),
                name="product_product_export_supplier_matrix",
            ),
        ]
        return custom_urls + urls

    def export_supplier_matrix(self, request):
        return HttpResponse("Экспорт работает ✅")


@admin.register(ProductSupplier)
class ProductSupplierAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "supplier",
        "price_wholesale",
        "price_wholesale_final",
        "price_retail",
        "updated_at",
    )

    list_filter = ("supplier",)
    search_fields = (
        "product__title_sbt",
        "supplier__name",
        "supplier_prod_code",
    )

    autocomplete_fields = ("product", "supplier")


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    form = SupplierAdminForm

    search_fields = ("name",)

    list_display = (
        "name",
        "website",
        "contact_email",
        "whatsapp",
        "price_list_link",
        "iva_in_price",
        "ib_caba_in_prise",
    )

    def price_list_link(self, obj):
        if obj.price_list:
            return format_html('<a href="{}" target="_blank">Скачать</a>', obj.price_list.url)
        return "-"


@admin.register(ParserJob)
class ParserJobAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "last_status",
        "last_run_at",
        "last_success_at",
        "run_button",
        "log_link",
    )

    list_filter = ("last_status",)
    search_fields = ("name",)

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
        url = reverse("admin:web_parsers_app_parserjob_run_parser", args=[obj.pk])
        return format_html('<a class="button" href="{}">Запустить</a>', url)

    def log_link(self, obj):
        url = reverse("admin:web_parsers_app_parserjob_log", args=[obj.pk])
        return format_html('<a class="button" href="{}" target="_blank">Лог</a>', url)

    def run_parser(self, request, parser_id):
        parser = ParserJob.objects.get(pk=parser_id)
        changelist_url = reverse("admin:web_parsers_app_parserjob_changelist")

        parser.last_run_at = timezone.now()
        parser.last_status = "RUNNING"
        parser.last_error = ""
        parser.save()

        try:
            if parser.name == "ansal":
                run_ansal_parser.delay()
            else:
                run_web_parser.delay(parser.name)

            self.message_user(request, f"{parser.name} запущен 🚀")

        except Exception as e:
            parser.last_status = "ERROR"
            parser.last_error = str(e)
            parser.save()

            self.message_user(request, f"Ошибка: {e}", level=messages.ERROR)

        return redirect(changelist_url)

    def view_log(self, request, parser_id):
        parser = ParserJob.objects.get(pk=parser_id)

        # 🔥 фикс ansal_retail
        log_name = "ansal" if parser.name == "ansal_retail" else parser.name

        log_path = settings.BASE_DIR / "logs" / "parsers" / f"{log_name}.log"

        if not log_path.exists():
            raise Http404("Log file not found")

        return FileResponse(open(log_path, "rb"), content_type="text/plain")