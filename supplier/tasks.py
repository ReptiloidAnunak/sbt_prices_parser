from decimal import Decimal, InvalidOperation
from celery import shared_task

from supplier.models import Supplier
from product.models import ProductSupplier
from supplier.files_parsing.factory import get_parser
from options.models import Options


@shared_task
def process_price_list(supplier_id):
    supplier = Supplier.objects.get(id=supplier_id)
    file_path = supplier.price_list.path

    parser = get_parser(supplier)
    data = parser.parse(file_path)

    options = Options.load()
    dollar_rate = Decimal(str(options.dollar_rate))

    updated = 0
    not_found = 0
    errors = 0

    print(f"Обработано {len(data)} строк")
    print("-----------")
    print(data)

    for prod in data:
        try:
            code = prod.get("code")
            title = prod.get("title")
            raw_price = prod.get("price")
            currency = str(prod.get("currency") or supplier.currency or "ARS").upper().strip()

            if not code:
                continue

            prod_supplier = ProductSupplier.objects.filter(
                supplier=supplier,
                supplier_prod_code=str(code).strip()
            ).first()

            if not prod_supplier:
                not_found += 1
                continue

            price = None
            if raw_price is not None:
                try:
                    price = Decimal(str(raw_price))
                except (InvalidOperation, ValueError, TypeError):
                    errors += 1
                    continue

                if currency == "USD":
                    price = price * dollar_rate

            prod_supplier.supplier_prod_title = str(title).strip()[:255] if title else ""
            prod_supplier.price_wholesale = price
            prod_supplier.save()

            updated += 1

        except Exception as e:
            errors += 1
            print(f"Ошибка обработки товара {prod}: {e}")

    return {
        "updated": updated,
        "not_found": not_found,
        "errors": errors,
        "total": len(data),
    }