import json
import logging
from io import BytesIO
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

import pandas as pd

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
from django.utils import timezone

from options.models import Options
from product.models import ProductSupplier
from supplier.models import Supplier


logger = logging.getLogger(__name__)

VALID_PRICE_TYPES = {"wholesale", "retail"}


def clean_decimal(value):
    if value is None:
        return None

    value = str(value).strip()

    if not value or value.lower() in {"nan", "none", "null"}:
        return None

    value = (
        value
        .replace("$", "")
        .replace("ARS", "")
        .replace("U$S", "")
        .replace("USD", "")
        .replace(" ", "")
        .replace("\xa0", "")
        .strip()
    )

    # Если прилетело "6.194,66" — это аргентинский формат.
    # Если прилетело "6194.66" — это уже нормальный float/decimal формат.
    if "," in value:
        value = value.replace(".", "").replace(",", ".")

    try:
        return Decimal(value)
    except (InvalidOperation, ValueError):
        return None


def calculate_price_wholesale_final(price_wholesale, supplier):
    if price_wholesale is None:
        return None

    price = Decimal(str(price_wholesale))

    if supplier:
        if supplier.discount:
            discount = Decimal(str(supplier.discount))

            if discount > 1:
                discount = discount / Decimal("100")

            price = price * (Decimal("1") - discount)

        calc_base = price

        if not supplier.iva_in_price:
            price += calc_base * Decimal("0.21")

        if not supplier.ib_caba_in_prise:
            price += calc_base * Decimal("0.03")

    return price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def save_supplier_json_excel(supplier, rows):
    if not rows:
        return None

    df = pd.DataFrame(rows)

    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="api_import")

    output.seek(0)

    filename = f"{supplier.name.lower().replace(' ', '_')}_api_import.xlsx"

    supplier.price_list.save(
        filename,
        ContentFile(output.read()),
        save=False,
    )

    Supplier.objects.filter(pk=supplier.pk).update(
        price_list=supplier.price_list.name,
        upt_price_at=timezone.now(),
    )

    return supplier.price_list.name


def detect_price_type(data):
    price_type = str(data.get("price_type") or "").lower().strip()
    parser_name = str(data.get("parser_name") or "").lower().strip()

    if price_type:
        if price_type not in VALID_PRICE_TYPES:
            raise ValueError(
                f"Invalid price_type: {price_type}. "
                f"Allowed: {', '.join(sorted(VALID_PRICE_TYPES))}"
            )
        return price_type

    if parser_name.endswith("_retail"):
        return "retail"

    return "wholesale"


@csrf_exempt
def import_products(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    try:
        price_type = detect_price_type(data)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)

    supplier_name = data.get("supplier")
    parser_name = data.get("parser_name") or ""
    products_json_lst = data.get("products", [])

    if not supplier_name:
        return JsonResponse({"error": "supplier is required"}, status=400)

    supplier = Supplier.objects.filter(name__iexact=supplier_name).first()

    if not supplier:
        return JsonResponse(
            {"error": f"Supplier not found: {supplier_name}"},
            status=400,
        )

    options = Options.load()
    dollar_rate = Decimal(str(options.dollar_rate))

    updated = 0
    not_found = 0
    skipped = 0
    errors = 0

    excel_rows = []

    logger.info(
        f"Web import started | supplier={supplier.name} | "
        f"parser={parser_name} | price_type={price_type} | "
        f"currency={supplier.currency} | total={len(products_json_lst)}"
    )

    for item in products_json_lst:
        code = item.get("code")
        title = item.get("title")
        raw_price = item.get("price")
        url = item.get("url") or None
        currency = str(
            item.get("currency") or supplier.currency or "ARS"
        ).upper().strip()

        price_ars = None
        final_price = None
        row_status = ""
        row_error = ""

        try:
            # 1. Цена считается ВСЕГДА, даже если нет кода
            price = clean_decimal(raw_price)

            if price is None:
                skipped += 1
                row_status = "skipped"
                row_error = "Invalid price"

                logger.warning(
                    f"Invalid price | supplier={supplier.name} | "
                    f"parser={parser_name} | price_type={price_type} | "
                    f"code={code} | title={title} | price={raw_price}"
                )
                continue

            # 2. USD переводим в ARS
            if currency == "USD":
                price = price * dollar_rate

            price_ars = price

            if price_type == "wholesale":
                final_price = calculate_price_wholesale_final(price, supplier)

            # 3. Код проверяем ПОСЛЕ расчёта цены
            if not code:
                skipped += 1
                row_status = "skipped"
                row_error = "Missing code"

                logger.warning(
                    f"Missing code | supplier={supplier.name} | "
                    f"parser={parser_name} | price_type={price_type} | "
                    f"title={title} | price_ars={price_ars} | "
                    f"final_price={final_price}"
                )
                continue

            code = str(code).strip()

            product_price_obj = ProductSupplier.objects.filter(
                supplier=supplier,
                supplier_prod_code=code,
            ).first()

            if not product_price_obj:
                not_found += 1
                row_status = "not_found"
                row_error = "Code not found in ProductSupplier"

                logger.warning(
                    f"Not found | supplier={supplier.name} | "
                    f"parser={parser_name} | price_type={price_type} | "
                    f"code={code} | title={title} | "
                    f"price_ars={price_ars} | final_price={final_price}"
                )
                continue

            product_price_obj.supplier_prod_title = (
                str(title).strip()[:255] if title else ""
            )

            clean_url = str(url).strip() if url else None

            if clean_url:
                product_price_obj.link = clean_url

            if price_type == "retail":
                product_price_obj.price_retail = price

                update_fields = [
                    "price_retail",
                    "supplier_prod_title",
                ]

                if clean_url:
                    update_fields.append("link")

                product_price_obj.save(update_fields=update_fields)

            else:
                product_price_obj.price_wholesale = price
                product_price_obj.price_wholesale_final = final_price

                update_fields = [
                    "price_wholesale",
                    "price_wholesale_final",
                    "supplier_prod_title",
                ]

                if clean_url:
                    update_fields.append("link")

                product_price_obj.save(update_fields=update_fields)

            updated += 1
            row_status = "updated"

        except Exception as e:
            errors += 1
            row_status = "error"
            row_error = str(e)

            logger.exception(
                f"Import error | supplier={supplier.name} | "
                f"parser={parser_name} | price_type={price_type} | "
                f"item={item} | error={e}"
            )

        finally:
            excel_rows.append(
                {
                    "supplier": supplier.name,
                    "parser_name": parser_name,
                    "price_type": price_type,
                    "code": code,
                    "title_original": title,
                    "price_original": raw_price,
                    "currency": currency,
                    "dollar_rate": dollar_rate,
                    "price_ars": price_ars,
                    "price_wholesale_final": final_price,
                    "status": row_status,
                    "error": row_error,
                }
            )

    excel_file = save_supplier_json_excel(supplier, excel_rows)

    logger.info(
        f"Web import finished | supplier={supplier.name} | "
        f"parser={parser_name} | price_type={price_type} | "
        f"updated={updated} | not_found={not_found} | "
        f"skipped={skipped} | errors={errors}"
    )

    return JsonResponse(
        {
            "status": "ok",
            "supplier": supplier.name,
            "parser_name": parser_name,
            "price_type": price_type,
            "updated": updated,
            "not_found": not_found,
            "skipped": skipped,
            "errors": errors,
            "total": len(products_json_lst),
            "excel_saved": bool(excel_file),
            "excel_file": excel_file,
        }
    )