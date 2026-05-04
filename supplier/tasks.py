from decimal import Decimal, InvalidOperation

from celery import shared_task
from rapidfuzz import process, fuzz

from supplier.models import Supplier
from product.models import ProductSupplier
from supplier.files_parsing.factory import get_parser
from options.models import Options

import re


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

def normalize_title(s: str) -> str:
    if not s:
        return ""

    s = str(s).upper()

    s = s.replace("\xa0", " ")

    s = re.sub(r"\s+X\s+", " ", s)

    s = re.sub(r"[^A-Z0-9\. ]", " ", s)

    s = re.sub(r"\s+", " ", s)

    s = re.sub(r"(\d)\s+KG", r"\1KG", s)

    return s.strip()


def match_by_title(title, titles, title_map, threshold=70):
    if not title:
        return None

    title_norm = normalize_title(title)

    match = process.extractOne(
        title_norm,
        titles,
        scorer=fuzz.token_set_ratio
    )

    match = process.extractOne(
    normalize_title(title),
    titles,
    scorer=fuzz.token_set_ratio
)

    print("DEBUG MATCH:", title, "=>", match)

    if not match:
        return None

    best_title, score, _ = match

    if score < threshold:
        return None

    return title_map.get(best_title)


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

    # ==========================
    # PRELOAD ВСЕ ТОВАРЫ
    # ==========================
    all_products = ProductSupplier.objects.filter(
        supplier=supplier
    ).only("id", "supplier_prod_code", "supplier_prod_title")

    # title → object map
    title_map = {
        normalize_title(p.supplier_prod_title): p
        for p in all_products
        if p.supplier_prod_title
    }

    titles = list(title_map.keys())

    for prod in data:
        try:
            code = str(prod.get("code") or "").strip()
            title = prod.get("title")
            raw_price = prod.get("price")
            currency = str(
                prod.get("currency") or supplier.currency or "ARS"
            ).upper().strip()

            price = to_decimal(raw_price)

            if raw_price is not None and price is None:
                errors += 1
                print(f"Ошибка цены: {prod}")
                continue

            if price is not None and currency == "USD":
                price = price * dollar_rate

            prod_supplier = None

            # ==========================
            # 1. MATCH ПО CODE (ПРИОРИТЕТ)
            # ==========================
            if code:
                prod_supplier = ProductSupplier.objects.filter(
                    supplier=supplier,
                    supplier_prod_code=code,
                ).first()

            # ==========================
            # 2. FALLBACK: FUZZY TITLE
            # ==========================
            if not prod_supplier:
                prod_supplier = match_by_title(
                    title,
                    titles,
                    title_map,
                    threshold=85
                )

            # ==========================
            # NOT FOUND
            # ==========================
            if not prod_supplier:
                not_found += 1
                print(f"Не найден ProductSupplier: code={code} | {title} | price={price}")
                continue

            # ==========================
            # UPDATE
            # ==========================
            prod_supplier.supplier_prod_title = str(title).strip()[:255] if title else ""
            prod_supplier.price_wholesale = price

            prod_supplier.save()  # пересчёт final price внутри модели

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