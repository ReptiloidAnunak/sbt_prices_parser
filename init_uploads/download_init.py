import os
import django
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api_server.settings")
django.setup()

import pandas as pd
from supplier.models import Supplier
from product.models import Product

def load_suppliers():
    file_path = "init_uploads/download_files/Копия Список поставщиков.xlsx"

    df = pd.read_excel(file_path, header=1)
    df.columns = df.columns.str.strip()
    df = df.dropna(how="all")

    for row in df.to_dict(orient="records"):
        name = row.get("Название")
        site = row.get("Сайт")

        if pd.isna(name):
            continue

        name = str(name).strip()
        if not name or name.lower() == "nan":
            continue

        if pd.isna(site):
            site = None
        else:
            site = str(site).strip()
            if not site or site.lower() == "nan":
                site = None
            elif not site.startswith(("http://", "https://")):
                site = "https://" + site

        print(name, site)

        Supplier.objects.create(
            name=name,
            website=site
        )


import pandas as pd
from product.models import Product


def clean_category(cat: str) -> str:
    return cat.replace("*", "").strip().lower()


def import_products_from_excel():
    file_path = "init_uploads/download_files/all_prods.xlsx"

    df = pd.read_excel(file_path, header=0)

    df.columns = df.columns.str.strip()

    df = df.dropna(how="all")

    print("📊 Колонки:", df.columns.tolist())

    if "Категория товара" not in df.columns or "Наименование" not in df.columns:
        print("❌ Нет нужных колонок в файле!")
        return

    valid_categories = {c for c, _ in Product._meta.get_field("category").choices}

    normalized_valid = {
        clean_category(c): c for c in valid_categories
    }

    products_to_create = []

    for row in df.to_dict(orient="records"):
        raw_category = str(row.get("Категория товара", "")).strip()
        title = str(row.get("Наименование", "")).strip()

        if not title:
            continue

        norm_category = clean_category(raw_category)

        if norm_category not in normalized_valid:
            print(f"⚠️ Пропуск: '{title}' → неизвестная категория '{raw_category}'")
            continue

        category = normalized_valid[norm_category]

        products_to_create.append(
            Product(
                category=category,
                title_sbt=title
            )
        )

    unique_products = {}
    for p in products_to_create:
        unique_products[p.title_sbt] = p

    products = list(unique_products.values())

    Product.objects.bulk_create(products)

    print(f"✅ Загружено товаров: {len(products)}")


def run():
    load_suppliers()
    import_products_from_excel()


run()