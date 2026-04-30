import json
import os
import random
import time

from bs4 import BeautifulSoup
import requests

from web_parsers_app.logger import get_logger
from web_parsers_app.send_json import send_products_json
from web_parsers_app.settings import get_json_file, get_supplier_name


PARSER_NAME = "bellini_retail"

logger = get_logger(PARSER_NAME)

JSON_FILE = get_json_file(PARSER_NAME)
SUPPLIER_NAME = get_supplier_name(PARSER_NAME)

BASE_URL = "https://www.bellinihnos.com.ar"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/webp,*/*;q=0.8"
    ),
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
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


def sleep_random(a=6, b=14):
    delay = random.uniform(a, b)
    logger.info(f"Sleep {delay:.1f}s")
    time.sleep(delay)


def clean_text(value):
    if value is None:
        return ""

    return " ".join(str(value).replace("\xa0", " ").split())


def parse_price(value):
    if not value:
        return None

    value = clean_text(value)

    value = (
        value.replace("$", "")
        .replace("ARS", "")
        .replace("U$S", "")
        .replace("USD", "")
        .replace(" ", "")
        .replace("\xa0", "")
        .strip()
    )

    # Bellini обычно: 78,933.12 -> 78933.12
    if "," in value and "." in value:
        if value.find(",") < value.find("."):
            value = value.replace(",", "")
        else:
            value = value.replace(".", "").replace(",", ".")
    elif "," in value:
        value = value.replace(",", ".")
    elif "." in value:
        parts = value.split(".")
        if len(parts) > 1 and len(parts[-1]) == 3:
            value = value.replace(".", "")

    try:
        return f"{float(value):.2f}"
    except ValueError:
        logger.warning(f"Could not parse Bellini price: {value}")
        return None


def safe_get(session, url, retries=5):
    for attempt in range(1, retries + 1):
        try:
            response = session.get(
                url,
                headers=HEADERS,
                timeout=40,
            )

            if response.status_code == 429:
                wait = random.uniform(30, 70)
                logger.warning(
                    f"429 Too Many Requests | attempt={attempt}/{retries} | "
                    f"sleep={wait:.1f}s | url={url}"
                )
                time.sleep(wait)
                continue

            response.raise_for_status()
            return response

        except requests.exceptions.RequestException as e:
            wait = random.uniform(15, 35)
            logger.warning(
                f"Request error | attempt={attempt}/{retries} | "
                f"sleep={wait:.1f}s | url={url} | error={e}"
            )
            time.sleep(wait)

    raise RuntimeError(f"Failed to download after retries: {url}")


def warmup_session(session):
    try:
        logger.info("Warmup Bellini session")
        safe_get(session, BASE_URL, retries=3)
        sleep_random(5, 10)
    except Exception as e:
        logger.warning(f"Warmup failed, continue anyway: {e}")


def get_products(session, link):
    response = safe_get(session, link)
    soup = BeautifulSoup(response.content, "html.parser")

    prods_grid = soup.find("div", class_="products")
    if not prods_grid:
        logger.warning(f"No products grid: {link}")
        return []

    prods_cards = prods_grid.find_all("div", class_="product-small")
    result = []

    for card in prods_cards:
        try:
            sku_div = card.find("div", class_="custom-product-sku")
            text_box = card.find("div", class_="box-text")

            if not sku_div or not text_box:
                continue

            title_tag = text_box.find("a")
            price_tag = text_box.find("bdi")

            if not title_tag or not price_tag:
                continue

            sku = clean_text(sku_div.get_text())
            title = clean_text(title_tag.get_text())
            url = title_tag.get("href", "").strip()
            price = parse_price(price_tag.get_text(" ", strip=True))

            if not sku or not title or price is None:
                logger.warning(
                    f"Skip Bellini product: sku={sku}, title={title}, price={price}"
                )
                continue

            result.append(
                {
                    "code": sku,
                    "title": title,
                    "price": price,
                    "url": url,
                    "currency": "ARS",
                }
            )

        except Exception as e:
            logger.warning(f"Skip Bellini card: {e}")
            continue

    logger.info(f"Products found on page: {len(result)} | {link}")
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

    session = requests.Session()
    session.headers.update(HEADERS)

    try:
        warmup_session(session)

        for link in categories_links:
            logger.info(f"Parse: {link}")

            products = get_products(session, link)
            all_products.extend(products)

            sleep_random(8, 18)

        save_to_json(all_products)

        api_result = send_products_json(
            JSON_FILE,
            SUPPLIER_NAME,
            parser_name=PARSER_NAME,
            price_type="retail",
        )

        logger.info(
            f"{PARSER_NAME} parsing finished. "
            f"Products: {len(all_products)}. API result: {api_result}"
        )

        return {
            "status": "ok",
            "supplier": SUPPLIER_NAME,
            "parser_name": PARSER_NAME,
            "price_type": "retail",
            "products": len(all_products),
        }

    except Exception as e:
        logger.exception(f"Bellini parser failed: {e}")
        raise


if __name__ == "__main__":
    run()