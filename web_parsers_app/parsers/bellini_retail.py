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

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Connection": "keep-alive",
}

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
    page_html = requests.get(link, headers=HEADERS, timeout=30)
    page_html.raise_for_status()

    soup = BeautifulSoup(page_html.content, "html.parser")

    prods_grid = soup.find("div", class_="products")
    if not prods_grid:
        logger.warning(f"No products grid: {link}")
        return []

    prods_cards = prods_grid.find_all("div", class_="product-small")

    result = []

    for card in prods_cards:
        sku_div = card.find("div", class_="custom-product-sku")
        text_box = card.find("div", class_="box-text")

        if not sku_div or not text_box:
            continue

        title_tag = text_box.find("a")
        price_tag = text_box.find("bdi")

        if not title_tag or not price_tag:
            continue

        sku = sku_div.text.strip()
        title = title_tag.text.strip()
        url = title_tag["href"]
        price = price_tag.text.strip().strip("$").strip().replace(",", "")

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
    logger.info("Bellini retail parser started")

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