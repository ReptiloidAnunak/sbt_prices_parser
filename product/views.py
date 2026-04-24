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
import logging

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
    print(f'POST: {request}', flush=True)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    supplier_name = data.get("supplier")
    products_json_lst = data.get("products", [])

    if not supplier_name:
        return JsonResponse({"error": "supplier is required"}, status=400)

    supplier, _ = Supplier.objects.get_or_create(name=supplier_name)
    options = Options.load()
    dollar_rate = Decimal(str(options.dollar_rate))
    logger.info(f'Supperier: {supplier.name} currency: {supplier.currency}')
    df = pd.DataFrame(products_json_lst)

    updated = 0
    not_found = 0
    errors = 0

    for item in products_json_lst:
        try:
            code = item.get("code")
            title = item.get("title")
            raw_price = item.get("price")
            currency = str(item.get("currency") or supplier.currency or "ARS").upper().strip()

            if not code:
                continue

            price = clean_decimal(raw_price)
            if price is None:
                logger.warning(
                    f"Empty or invalid price for supplier={supplier_name}, code={code}, title={title}"
                )
                continue

            if currency == "USD":
                price = price * dollar_rate

            product_price_obj = ProductSupplier.objects.filter(
                supplier=supplier,
                supplier_prod_code=str(code).strip()
            ).first()

            if not product_price_obj:
                not_found += 1
                logger.warning(
                    f"Not found for supplier={supplier_name}, code={code}, title={title}"
                )
                continue

            product_price_obj.price_wholesale = price
            product_price_obj.supplier_prod_title = str(title).strip()[:255] if title else ""
            product_price_obj.save()

            updated += 1
            logger.info(
                f"Updated: {product_price_obj.product.title_sbt} | code={code} | currency={currency} | price={price}"
            )

        except Exception as e:
            errors += 1
            logger.exception(
                f"Import error | supplier={supplier_name} | item={item} | error={e}"
            )

    try:
        buffer = BytesIO()
        df.to_excel(buffer, index=False)
        buffer.seek(0)

        filename = f"products_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx"

        supplier.price_list.save(
            filename,
            ContentFile(buffer.read()),
            save=True
        )
    except Exception as e:
        logger.exception(
            f"Failed to save uploaded xlsx for supplier={supplier_name}: {e}"
        )

    return JsonResponse({
        "status": "ok",
        "supplier": supplier_name,
        "updated": updated,
        "not_found": not_found,
        "errors": errors,
        "total": len(products_json_lst),
    })