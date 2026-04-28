import json
import os
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from web_parsers_app.logger import get_logger
from web_parsers_app.settings import get_json_file, get_supplier_name
from web_parsers_app.send_json import send_products_json


PARSER_NAME = "reld_retail"
logger = get_logger(PARSER_NAME)

JSON_FILE = get_json_file(PARSER_NAME)
SUPPLIER_NAME = get_supplier_name(PARSER_NAME)

BASE_URL = "https://www.reld.com.ar"
GRID_URL = f"{BASE_URL}/index_grilla.php"

PARAMS = {
    "agru_1": "",
    "agru_2": "",
    "agru_3": "",
    "articulo": "",
    "destaca": "",
    "modo_grilla": "S",
    "cant_x_pagina": "10000",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) "
        "Gecko/20100101 Firefox/125.0"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
}


def clean_text(value):
    if value is None:
        return ""

    return " ".join(str(value).replace("\xa0", " ").split())


def parse_price(value):
    """
    '$ 6.194,66' -> 6194.66
    '$6.194'    -> 6194.0
    ''          -> None
    """
    value = clean_text(value)

    if not value:
        return None

    value = (
        value.replace("$", "")
        .replace("ARS", "")
        .replace("U$S", "")
        .replace("USD", "")
        .replace(" ", "")
        .strip()
    )

    value = re.sub(r"[^\d,.-]", "", value)

    if not value:
        return None

    if "," in value:
        value = value.replace(".", "").replace(",", ".")

    try:
        return float(value)
    except ValueError:
        logger.warning(f"Could not parse price: {value}")
        return None


def download_html():
    logger.info("Downloading RELD retail products page")

    with requests.Session() as session:
        response = session.get(
            GRID_URL,
            params=PARAMS,
            headers=HEADERS,
            timeout=60,
        )

        # У RELD в HTML указан ISO-8859-1
        response.encoding = "ISO-8859-1"
        response.raise_for_status()

        logger.info(f"Downloaded HTML size: {len(response.text)}")

        return response.text


def extract_code_from_url(url):
    if not url:
        return ""

    match = re.search(r"cod_articulo=([^&]+)", url)

    if match:
        return clean_text(match.group(1))

    return ""


def get_prods(html):
    soup = BeautifulSoup(html, "html.parser")
    products = []

    rows = soup.select('tr[id^="row-"]')
    logger.info(f"Found rows: {len(rows)}")

    for row in rows:
        try:
            cols = row.select("td")

            if len(cols) < 5:
                continue

            title_link = cols[1].select_one('a[href*="articulo.php?cod_articulo="]')
            code_link = cols[2].select_one('a[href*="articulo.php?cod_articulo="]')
            price_cell = row.select_one("td.carrito-precio")

            if not code_link:
                continue

            href = code_link.get("href", "")
            url = urljoin(BASE_URL, href)

            code = clean_text(code_link.get_text())
            title = clean_text(title_link.get_text()) if title_link else ""
            price = parse_price(price_cell.get_text()) if price_cell else None

            if not code:
                code = extract_code_from_url(href)

            if not code and not title:
                continue

            products.append(
                {
                    "code": code,
                    "url": url,
                    "title": title,
                    "price": price,
                    "currency": "ARS",
                }
            )

        except Exception as e:
            logger.warning(f"Skip RELD retail product row: {e}")
            continue

    return products

def save_to_json(prods, json_file=JSON_FILE):
    os.makedirs(os.path.dirname(json_file), exist_ok=True)

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(prods, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved {len(prods)} products to {json_file}")

    return len(prods)


def run():
    logger.info("RELD retail parser started")

    try:
        html = download_html()
        products = get_prods(html)

        total_products = save_to_json(products)

        api_result = send_products_json(
            JSON_FILE,
            SUPPLIER_NAME,
            parser_name=PARSER_NAME,
        )

        logger.info(
            f"RELD retail parsing finished. "
            f"Total products: {total_products}. API result: {api_result}"
        )

        return {
            "status": "ok",
            "supplier": SUPPLIER_NAME,
            "parser_name": PARSER_NAME,
            "price_type": "retail",
            "products": total_products,
            "api_result": api_result,
        }

    except Exception as e:
        logger.exception(f"RELD retail parser failed: {e}")
        raise


if __name__ == "__main__":
    run()