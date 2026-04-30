import json
import os
import time
import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from bs4 import BeautifulSoup
import requests

from web_parsers_app.logger import get_logger
from web_parsers_app.send_json import send_products_json
from web_parsers_app.settings import get_json_file, get_supplier_name


PARSER_NAME = "refrigeracion_norte_retail"

logger = get_logger(PARSER_NAME)

JSON_FILE = get_json_file(PARSER_NAME)
SUPPLIER_NAME = get_supplier_name(PARSER_NAME)

BASE_URL = "https://refrigeracionnorte.com.ar"

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


def parse_price(value):
    if not value:
        return None

    raw = str(value).strip()

    value = (
        raw.replace("$", "")
        .replace("ARS", "")
        .replace("U$S", "")
        .replace("USD", "")
        .replace(" ", "")
        .replace("\xa0", "")
        .strip()
    )

    value = re.sub(r"[^\d,.-]", "", value)

    if not value:
        return None

    # AR: 711.182,50 -> 711182.50
    if "," in value and "." in value:
        if value.find(".") < value.find(","):
            value = value.replace(".", "").replace(",", ".")
        else:
            value = value.replace(",", "")

    # AR: 711,50 -> 711.50
    elif "," in value:
        value = value.replace(",", ".")

    # AR thousands: 711.182 -> 711182
    elif "." in value:
        parts = value.split(".")
        if len(parts) > 1 and len(parts[-1]) == 3:
            value = value.replace(".", "")

    try:
        return str(Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    except (InvalidOperation, ValueError):
        logger.warning(f"Could not parse price: raw={raw}, cleaned={value}")
        return None


def get_products():
    result = []

    page_html = requests.get(
        f"{BASE_URL}/page/1/",
        headers=HEADERS,
        timeout=30,
    )
    page_html.raise_for_status()

    soup = BeautifulSoup(page_html.content, "html.parser")

    page_numbers = soup.find_all("a", class_="page-numbers")
    last_page = int(page_numbers[-2].text.strip()) if len(page_numbers) >= 2 else 1

    pages_links = [
        f"{BASE_URL}/page/{n}/"
        for n in range(1, last_page + 1)
    ]

    for link in pages_links:
        logger.info(f"Parse: {link}")

        page_html = requests.get(link, headers=HEADERS, timeout=30)
        page_html.raise_for_status()

        soup = BeautifulSoup(page_html.content, "html.parser")

        prods_grid = soup.find("div", class_="products-container")
        if not prods_grid:
            logger.warning(f"No products grid: {link}")
            continue

        prods_cards = prods_grid.find_all("div", class_="product")

        for card in prods_cards:
            try:
                add_btn = card.find("a", class_="add_to_cart_button")
                sku = add_btn.get("data-product_sku") if add_btn else None

                title_tag = card.find("a", {"aria-label": "Post Title"})
                if not title_tag:
                    continue

                title = title_tag.get_text(" ", strip=True)
                url = title_tag.get("href", "").strip()

                price_tag = card.find("bdi")
                price = parse_price(price_tag.get_text(" ", strip=True)) if price_tag else None

                if not sku or not title or price is None:
                    logger.warning(
                        f"Skip Refrigeracion Norte product: sku={sku}, title={title}, price={price}"
                    )
                    continue

                result.append({
                    "code": sku,
                    "title": title,
                    "price": price,
                    "url": url,
                    "currency": "ARS",
                })

            except Exception as e:
                logger.warning(f"Skip Refrigeracion Norte product card: {e}")
                continue

        time.sleep(1)

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
    logger.info("Refrigeracion Norte retail parser started")

    clear_json()

    try:
        products = get_products()

        save_to_json(products)

        api_result = send_products_json(
            JSON_FILE,
            SUPPLIER_NAME,
            parser_name=PARSER_NAME,
            price_type="retail",
        )

        logger.info(
            f"{PARSER_NAME} parsing finished. "
            f"Products: {len(products)}. API result: {api_result}"
        )

        return {
            "status": "ok",
            "supplier": SUPPLIER_NAME,
            "parser_name": PARSER_NAME,
            "price_type": "retail",
            "products": len(products),
        }

    except Exception as e:
        logger.exception(f"Refrigeracion Norte retail parser failed: {e}")
        raise


if __name__ == "__main__":
    run()