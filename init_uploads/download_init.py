import os
import sys
import re
import django
import pandas as pd
import math
from django.db.utils import IntegrityError

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api_server.settings")
django.setup()

from supplier.models import Supplier
from product.models import Product, ProductSupplier
from mercado_libre.models import MercadoLibreShop
from options.models import Options
import logging

logger = logging.getLogger(__name__)

# -------------------- CONFIG --------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PRODS_CODES_FILE = "prods_codes.xlsx"

SUPPLIERS_FILE = os.path.join(BASE_DIR, "download_files", "Копия Список поставщиков.xlsx")
PRODUCTS_FILE = os.path.join(BASE_DIR, PRODS_CODES_FILE)
SUPPLIER_LINKS_FILE = PRODUCTS_FILE
MERCADO_SHOPS_FILE = os.path.join(BASE_DIR, "download_files", "mercado_shops.xlsx")


# -------------------- HELPERS --------------------

def normalize_text(value: str) -> str:
    value = str(value).strip().lower()
    value = value.replace("ё", "е")
    value = re.sub(r"\s+", " ", value)
    return value


def normalize_supplier_name(value: str) -> str:
    value = normalize_text(value)
    value = value.replace('"', "")
    value = re.sub(r"[^\w\s]", " ", value)
    value = re.sub(r"\b(srl|sa|s a|s\.a\.|sr l)\b", "", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def clean_category(cat: str) -> str:
    return str(cat).replace("*", "").strip().lower()


def clean_int(value):
    if pd.isna(value):
        return None

    if isinstance(value, float):
        if value.is_integer():
            return int(value)
        return None

    if isinstance(value, int):
        return value

    value = str(value).strip()

    if not value or value.lower() == "nan":
        return None

    try:
        return int(float(value))
    except ValueError:
        return None


def clean_code(value):
    if pd.isna(value):
        return None

    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return str(value)

    if isinstance(value, int):
        return str(value)

    value = str(value).strip()

    if not value or value.lower() == "nan":
        return None

    return value


def clean_title(value):
    if pd.isna(value):
        return None

    value = str(value).strip()

    if not value or value.lower() in {"nan", "none", "not_found"}:
        return None

    return value


def clean_value(value):
    if pd.isna(value):
        return None

    value = str(value).strip()

    if not value or value.lower() == "nan":
        return None

    return value


def clean_link(value):
    value = clean_value(value)
    if not value:
        return None

    if not value.startswith(("http://", "https://")):
        value = "https://" + value

    return value


def get_existing_products_map():
    return {
        p.title_sbt: p
        for p in Product.objects.all().only("id", "title_sbt")
    }


def get_productsupplier_field_names():
    return {f.name for f in ProductSupplier._meta.fields}


# -------------------- SUPPLIERS --------------------

def load_suppliers():
    df = pd.read_excel(SUPPLIERS_FILE, header=1)
    df.columns = df.columns.str.strip()
    df = df.dropna(how="all")

    for row in df.to_dict(orient="records"):
        name = row.get("Название")
        site = row.get("Сайт")
        discount = row.get("Скидка %")
        iva = row.get("IVA")
        currency = row.get("Валюта")
        login = row.get("Логин")
        password = row.get("Пароль")

        if pd.isna(name):
            continue

        name = str(name).strip()
        if not name or name.lower() == "nan":
            continue

        site = clean_link(site)

        iva = not pd.isna(iva)

        discount = None if pd.isna(discount) else float(discount)

        if pd.isna(currency):
            currency = "ARS"
        else:
            currency = str(currency).strip().upper()
            if currency not in ["ARS", "USD"]:
                currency = "ARS"

        login = clean_value(login)
        password = clean_value(password)

        Supplier.objects.update_or_create(
            name=name,
            defaults={
                "website": site,
                "discount": discount,
                "iva_in_price": iva,
                "currency": currency,
                "login": login,
                "password": password,
            },
        )

# -------------------- PRODUCTS --------------------

def fix_nan(value):
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def import_products_from_excel():
    df = pd.read_excel(PRODUCTS_FILE, header=0)
    df.columns = df.columns.str.strip()
    df = df.dropna(how="all")

    print("📊 Колонки:", df.columns.tolist())

    if "Категория товара" not in df.columns or "Наименование" not in df.columns:
        print("❌ Нет нужных колонок в файле!")
        return

    valid_categories = {c for c, _ in Product._meta.get_field("category").choices}
    normalized_valid = {clean_category(c): c for c in valid_categories}

    created_count = 0
    updated_count = 0

    for row in df.to_dict(orient="records"):
        code_sbt = clean_int(row.get("Код [KOD]"))
        price = fix_nan(row.get('Цена "Розница AR"'))
        if price is not None:
            price = int(price)

        title = str(row.get("Наименование", "")).strip()
        raw_category = str(row.get("Категория товара", "")).strip()

        if not title:
            continue

        norm_category = clean_category(raw_category)

        if norm_category not in normalized_valid:
            print(f"⚠️ Пропуск: '{title}' → неизвестная категория '{raw_category}'")
            continue

        category = normalized_valid[norm_category]

        obj, created = Product.objects.get_or_create(
            title_sbt=title,
            defaults={
                "code_sbt": code_sbt,
                "category": category,
                "price_sbt": price,
            }
        )

        if created:
            created_count += 1
            print(f"✅ CREATED: {obj.title_sbt} | price={obj.price_sbt}")
        else:
            changed = False

            if code_sbt is not None and obj.code_sbt != code_sbt:
                obj.code_sbt = code_sbt
                changed = True

            if obj.category != category:
                obj.category = category
                changed = True

            if price is not None and obj.price_sbt != price:
                obj.price_sbt = price
                changed = True

            if changed:
                obj.save()
                updated_count += 1

            print(f"🔄 UPDATED: {obj.title_sbt} | price={obj.price_sbt}")

    print(f"✅ Products created: {created_count}")
    print(f"✅ Products updated: {updated_count}")
    print(f"✅ Total products in DB: {Product.objects.count()}")


# -------------------- UNIVERSAL SUPPLIER LINKS --------------------

def build_supplier_lookup():
    """
    Возвращает словарь вида:
    {
        normalized_supplier_name: Supplier instance
    }
    """
    lookup = {}

    for supplier in Supplier.objects.all():
        normalized = normalize_supplier_name(supplier.name)
        lookup[normalized] = supplier

    alias_map = {
        "duna": ["duna", "duna srl"],
        "fijamom": ["fijamom"],
        "ansal": ["ansal"],
        "reld": ["reld"],
        "bellini": ["bellini"],
        "uriarte": ["uriarte"],
        "belgrano": ["belgrano"],
        "fluorgaz": ["fluorgaz"],
        "imi": ["imi"],
        "favale": ["favale"],
        "torrington": ["torrington"],
        "electrofrig": ["electrofrig"],
        "electrocity": ["electrocity"],
        "refrioil": ["refrioil"],
        "aieyo": ["aieyo"],
        "importadora nueva hera": ["importadora nueva hera"],
        "roma repuestos insumos": ["roma repuestos insumos"],
        "oeste service": ["oeste service", "oesteservice"],
        "distribuidora jc": ["distribuidora jc"],
        "distribuidora deyce": ["distribuidora deyce"],
        "dpmg anton": ["dpmg anton", "anton"],
        "tidar": ["tidar"],
        "casa jarse": ["casa jarse"],
        "lujumar": ["lujumar", "lujumar srl"],
        "norfrig": ["norfrig"],
        "pilisar": ["pilisar"],
        "skf": ["skf"],
        "industrias mct": ["industrias mct"],
        "guillermo pini": ["guillermo pini", "pini"],
        "damfer": ["damfer"],
    }

    resolved_lookup = {}

    for canonical, variants in alias_map.items():
        found_supplier = None
        for variant in variants:
            normalized_variant = normalize_supplier_name(variant)
            if normalized_variant in lookup:
                found_supplier = lookup[normalized_variant]
                break

        if found_supplier:
            resolved_lookup[canonical] = found_supplier

    for normalized_name, supplier in lookup.items():
        resolved_lookup.setdefault(normalized_name, supplier)

    return resolved_lookup


def discover_supplier_prefixes(df: pd.DataFrame):
    """
    Ищем все префиксы поставщиков по колонкам:
    '<prefix> код'
    '<prefix> название'
    """
    prefixes = set()

    for col in df.columns:
        col_clean = str(col).strip()

        if col_clean.endswith(" код"):
            prefix = col_clean[:-4].strip()
            if prefix:
                prefixes.add(prefix)

        elif col_clean.endswith(" название"):
            prefix = col_clean[:-9].strip()
            if prefix:
                prefixes.add(prefix)

    return sorted(prefixes)


def resolve_supplier_by_prefix(prefix: str, supplier_lookup: dict):
    normalized_prefix = normalize_supplier_name(prefix)

    if normalized_prefix in supplier_lookup:
        return supplier_lookup[normalized_prefix]

    for key, supplier in supplier_lookup.items():
        if key == normalized_prefix:
            return supplier
        if key.startswith(normalized_prefix) or normalized_prefix.startswith(key):
            return supplier

    return None


def load_prods_suppliers_codes_titles():
    df = pd.read_excel(SUPPLIER_LINKS_FILE)
    df.columns = [str(c).strip() for c in df.columns]

    if "Наименование" not in df.columns:
        print("❌ В файле нет колонки 'Наименование'")
        return

    supplier_prefixes = discover_supplier_prefixes(df)
    print("📦 Найдены поставщики в таблице:", supplier_prefixes)

    supplier_lookup = build_supplier_lookup()
    ps_fields = get_productsupplier_field_names()
    products_map = get_existing_products_map()

    created_or_updated = 0

    for _, row in df.iterrows():
        product_title = str(row.get("Наименование", "")).strip()

        if not product_title:
            continue

        product = products_map.get(product_title)

        if not product:
            print(f"❌ Product not found: {product_title}")
            continue

        for prefix in supplier_prefixes:
            supplier = resolve_supplier_by_prefix(prefix, supplier_lookup)

            if not supplier:
                print(f"⚠️ Поставщик не найден в БД для префикса: {prefix}")
                continue

            code_col = f"{prefix} код"
            title_col = f"{prefix} название"

            supplier_code = clean_code(row.get(code_col)) if code_col in df.columns else None
            supplier_title = clean_title(row.get(title_col)) if title_col in df.columns else None

            if not supplier_code and not supplier_title:
                continue

            defaults = {}

            if supplier_code:
                defaults["supplier_prod_code"] = supplier_code

            if supplier_title and "supplier_prod_title" in ps_fields:
                defaults["supplier_prod_title"] = supplier_title

            if not defaults:
                continue

            ProductSupplier.objects.update_or_create(
                product=product,
                supplier=supplier,
                defaults=defaults
            )

            created_or_updated += 1

    print(f"✅ Импорт связей завершён. Создано/обновлено: {created_or_updated}")


# -------------------- MERCADO LIBRE SHOPS --------------------

def load_mercado_libre_shops():
    df = pd.read_excel(MERCADO_SHOPS_FILE)
    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(how="all")

    print("📊 MercadoLibre колонки:", df.columns.tolist())

    if "Nombre" not in df.columns or "Link" not in df.columns:
        print("❌ В файле нет нужных колонок (Nombre / Link)")
        return

    created_count = 0
    updated_count = 0
    seen_names = {}

    for row in df.to_dict(orient="records"):
        name = clean_value(row.get("Nombre"))
        ml_page = clean_link(row.get("Link"))

        if not name:
            continue

        if name in seen_names and seen_names[name] != ml_page:
            print(f"⚠️ Дубль магазина: {name}")
            print(f"   Было: {seen_names[name]}")
            print(f"   Стало: {ml_page}")

        seen_names[name] = ml_page

        obj, created = MercadoLibreShop.objects.update_or_create(
            name=name,
            defaults={
                "ml_page": ml_page,
            }
        )

        if created:
            created_count += 1
            print(f"✅ ML CREATED: {obj.name} | {obj.ml_page}")
        else:
            updated_count += 1
            print(f"🔄 ML UPDATED: {obj.name} | {obj.ml_page}")

    print(f"✅ MercadoLibreShop created: {created_count}")
    print(f"✅ MercadoLibreShop updated: {updated_count}")
    print(f"✅ Total MercadoLibreShop in DB: {MercadoLibreShop.objects.count()}")


# -------------------- RUN --------------------

def run():
    logger.info('Initial loading')
    Options.load()
    load_suppliers()
    import_products_from_excel()
    load_prods_suppliers_codes_titles()
    load_mercado_libre_shops()
    logger.info('Initial info has been loaded')



run()