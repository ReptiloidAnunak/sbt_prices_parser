import json
import os
import time
from pathlib import Path

from bs4 import BeautifulSoup
import requests

from web_parsers_app.logger import get_logger
from web_parsers_app.send_json import send_products_json
from web_parsers_app.settings import get_json_file, get_supplier_name


PARSER_NAME = "bellini_retail"

logger = get_logger(PARSER_NAME)

JSON_FILE = get_json_file(PARSER_NAME)
SUPPLIER_NAME = get_supplier_name(PARSER_NAME)


categories_links = [
    "https://www.bellinihnos.com.ar/categoria-producto/compresores/",
    "https://www.bellinihnos.com.ar/categoria-producto/gas-refrigerante/",
    "https://www.bellinihnos.com.ar/categoria-producto/herramientas/",
    "https://www.bellinihnos.com.ar/categoria-producto/insumos-instalacion-aa/",
    "https://www.bellinihnos.com.ar/categoria-producto/metales/",
    "https://www.bellinihnos.com.ar/categoria-producto/refrigeracion-comercial/",
    "https://www.bellinihnos.com.ar/categoria-producto/repuestos-refrigeracion/",
    "https://www.bellinihnos.com.ar/categoria-producto/ventilacion/",
    "https://www.bellinihnos.com.ar/categoria-producto/ferreteria/",
]


def get_products(link):
    page_html = requests.get(link)
    soup = BeautifulSoup(page_html.content, 'html.parser')

    prods_grid = soup.find('div', class_="products")
    if not prods_grid:
        logger.warning(f"No products grid: {link}")
        return []

    prods_cards = prods_grid.find_all('div', class_='product-small')

    result = []

    for card in prods_cards:
        sku_div = card.find('div', class_='custom-product-sku')
        text_box = card.find('div', class_='box-text')

        if not sku_div or not text_box:
            continue

        sku = sku_div.text.strip()
        title = text_box.find('a').text.strip()
        url = text_box.find('a')['href']
        price = text_box.find('bdi').text.strip().strip('$').strip().replace(',', '')

        result.append({
            "code": sku,
            "title": title,
            "price": price,
            "url": url,
        })

    return result


def save_to_json(prods, json_file=JSON_FILE):
    os.makedirs(os.path.dirname(json_file), exist_ok=True)

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(prods, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved {len(prods)} products to JSON")


def clear_json(json_file=JSON_FILE):
    os.makedirs(os.path.dirname(json_file), exist_ok=True)

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)


def run():
    logger.info("Bellini parser started")

    clear_json()

    all_products = []

    try:
        for link in categories_links:
            logger.info(f"Parse: {link}")

            products = get_products(link)
            all_products.extend(products)

            time.sleep(2)

        save_to_json(all_products)

        send_products_json(JSON_FILE, SUPPLIER_NAME)

        return {
            "status": "ok",
            "supplier": SUPPLIER_NAME,
            "products": len(all_products),
        }

    except Exception as e:
        logger.exception(f"Bellini parser failed: {e}")
        raise


if __name__ == "__main__":
    run()