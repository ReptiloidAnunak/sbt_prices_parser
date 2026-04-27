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


def clean_decimal(value):
    if value is None:
        return None

    value = str(value).strip()

    if not value or value.lower() in {"nan", "none", "null"}:
        return None

    value = (
        value
        .replace("$", "")
        .replace(" ", "")
        .replace("\xa0", "")
        .replace(",", ".")
        .strip()
    )

    try:
        return Decimal(value)
    except (InvalidOperation, ValueError):
        return None


def calculate_price_wholesale_final(price_wholesale, supplier):
    if price_wholesale is None:
        return None

    price = Decimal(str(price_wholesale))

    if supplier:
        # 1. Скидка
        if supplier.discount:
            discount = Decimal(str(supplier.discount))

            # защита: если в базе 17 вместо 0.17
            if discount > 1:
                discount = discount / Decimal("100")

            price = price * (Decimal("1") - discount)

        # база для IVA и IB после скидки
        calc_base = price

        # 2. IVA 21%, если не включен
        if not supplier.iva_in_price:
            price += calc_base * Decimal("0.21")

        # 3. IB CABA 3%, если не включен
        if not supplier.ib_caba_in_prise:
            price += calc_base * Decimal("0.03")

    return price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def save_supplier_json_excel(supplier, rows):
    """
    Сохраняет результат API-импорта в Excel в Supplier.price_list.
    ВАЖНО: сохраняем через update(), чтобы не вызвать post_save и Celery.
    """

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


@csrf_exempt
def import_products(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    supplier_name = data.get("supplier")
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
        f"currency={supplier.currency} | total={len(products_json_lst)}"
    )

    for item in products_json_lst:
        code = item.get("code")
        title = item.get("title")
        raw_price = item.get("price")
        currency = str(item.get("currency") or supplier.currency or "ARS").upper().strip()

        price_ars = None
        final_price = None
        row_status = ""
        row_error = ""

        try:
            if not code:
                skipped += 1
                row_status = "skipped"
                row_error = "Missing code"
                logger.warning(f"Missing code | supplier={supplier.name} | item={item}")
                continue

            price = clean_decimal(raw_price)

            if price is None:
                skipped += 1
                row_status = "skipped"
                row_error = "Invalid price"
                logger.warning(
                    f"Invalid price | supplier={supplier.name} | "
                    f"code={code} | title={title} | price={raw_price}"
                )
                continue

            if currency == "USD":
                price = price * dollar_rate

            price_ars = price
            final_price = calculate_price_wholesale_final(price, supplier)

            product_price_obj = ProductSupplier.objects.filter(
                supplier=supplier,
                supplier_prod_code=str(code).strip(),
            ).first()

            if not product_price_obj:
                not_found += 1
                row_status = "not_found"
                row_error = "Code not found in ProductSupplier"
                logger.warning(
                    f"Not found | supplier={supplier.name} | code={code} | title={title}"
                )
                continue

            product_price_obj.price_wholesale = price
            product_price_obj.price_wholesale_final = final_price
            product_price_obj.supplier_prod_title = str(title).strip()[:255] if title else ""

            product_price_obj.save(
                update_fields=[
                    "price_wholesale",
                    "price_wholesale_final",
                    "supplier_prod_title",
                ]
            )

            updated += 1
            row_status = "updated"

        except Exception as e:
            errors += 1
            row_status = "error"
            row_error = str(e)

            logger.exception(
                f"Import error | supplier={supplier.name} | item={item} | error={e}"
            )

        finally:
            excel_rows.append(
                {
                    "supplier": supplier.name,
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
        f"updated={updated} | not_found={not_found} | skipped={skipped} | errors={errors}"
    )

    return JsonResponse(
        {
            "status": "ok",
            "supplier": supplier.name,
            "updated": updated,
            "not_found": not_found,
            "skipped": skipped,
            "errors": errors,
            "total": len(products_json_lst),
            "excel_saved": bool(excel_file),
            "excel_file": excel_file,
        }
    )