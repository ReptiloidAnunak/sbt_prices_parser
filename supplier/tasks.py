from decimal import Decimal, InvalidOperation

from celery import shared_task

from supplier.models import Supplier
from product.models import ProductSupplier
from supplier.files_parsing.factory import get_parser
from options.models import Options


def to_decimal(value):
    if value is None or value == "":
        return None

    try:
        value = str(value).strip()
        value = value.replace(" ", "")
        value = value.replace(",", ".")
        return Decimal(value)
    except (InvalidOperation, ValueError, TypeError):
        return None


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
    skipped = 0
    errors = 0

    print(f"Обработано {len(data)} строк")
    print("-----------")
    print(data)

    for prod in data:
        try:
            code = prod.get("code")
            title = prod.get("title")
            raw_price = prod.get("price")
            currency = str(
                prod.get("currency") or supplier.currency or "ARS"
            ).upper().strip()

            # цену считаем сразу, отдельно от кода
            price = to_decimal(raw_price)

            if raw_price is not None and price is None:
                errors += 1
                print(f"Ошибка цены: {prod}")
                continue

            if price is not None and currency == "USD":
                price = price * dollar_rate

            # без кода мы не можем найти ProductSupplier
            if not code:
                skipped += 1
                print(f"Пропущено: нет кода | {title} | price={price}")
                continue

            code = str(code).strip()

            prod_supplier = ProductSupplier.objects.filter(
                supplier=supplier,
                supplier_prod_code=code,
            ).first()

            if not prod_supplier:
                not_found += 1
                print(f"Не найден ProductSupplier: code={code} | {title} | price={price}")
                continue

            prod_supplier.supplier_prod_title = str(title).strip()[:255] if title else ""
            prod_supplier.price_wholesale = price

            # ВАЖНО:
            # save() должен пересчитать price_wholesale_final внутри модели ProductSupplier
            prod_supplier.save()

            updated += 1

        except Exception as e:
            errors += 1
            print(f"Ошибка обработки товара {prod}: {e}")

    return {
        "updated": updated,
        "not_found": not_found,
        "skipped": skipped,
        "errors": errors,
        "total": len(data),
    }