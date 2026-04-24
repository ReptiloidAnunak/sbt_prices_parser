from django.contrib import admin, messages
from django.utils.html import format_html

from .models import Product, ProductSupplier
from supplier.models import Supplier
from .forms import SupplierAdminForm
from mercado_libre.models import MercadoLibreProduct, MercadoLibreShop


from django.contrib import admin
from options.models import Options


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