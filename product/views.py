import json
import logging
from io import BytesIO
from decimal import Decimal, InvalidOperation
from datetime import datetime

import pandas as pd
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile

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

    value = value.replace("$", "").replace(",", ".").strip()

    try:
        return Decimal(value)
    except (InvalidOperation, ValueError):
        return None


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

    logger.info(
        f"Web import started | supplier={supplier.name} | "
        f"currency={supplier.currency} | total={len(products_json_lst)}"
    )

    for item in products_json_lst:
        try:
            code = item.get("code")
            title = item.get("title")
            raw_price = item.get("price")
            currency = str(item.get("currency") or supplier.currency or "ARS").upper().strip()

            if not code:
                skipped += 1
                logger.warning(f"Missing code | supplier={supplier.name} | item={item}")
                continue

            price = clean_decimal(raw_price)

            if price is None:
                skipped += 1
                logger.warning(
                    f"Invalid price | supplier={supplier.name} | "
                    f"code={code} | title={title} | price={raw_price}"
                )
                continue

            if currency == "USD":
                price = price * dollar_rate

            product_price_obj = ProductSupplier.objects.filter(
                supplier=supplier,
                supplier_prod_code=str(code).strip(),
            ).first()

            if not product_price_obj:
                not_found += 1
                logger.warning(
                    f"Not found | supplier={supplier.name} | code={code} | title={title}"
                )
                continue

            product_price_obj.price_wholesale = price
            product_price_obj.supplier_prod_title = str(title).strip()[:255] if title else ""
            product_price_obj.save(update_fields=["price_wholesale", "supplier_prod_title"])

            updated += 1

        except Exception as e:
            errors += 1
            logger.exception(
                f"Import error | supplier={supplier.name} | item={item} | error={e}"
            )

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
        }
    )