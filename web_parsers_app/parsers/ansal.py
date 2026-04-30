import json
import os
import random
import time
import re
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from playwright._impl._errors import TimeoutError, Error
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from supplier.models import Supplier
from web_parsers_app.logger import get_logger
from web_parsers_app.settings import (
    get_json_file,
    get_supplier_name,
    get_screen_shot_path,
)
from web_parsers_app.send_json import send_products_json


PARSER_NAME = "ansal"
logger = get_logger(PARSER_NAME)

JSON_FILE = get_json_file(PARSER_NAME)
SUPPLIER_NAME = get_supplier_name(PARSER_NAME)
SCREENSHOT_PATH = get_screen_shot_path(PARSER_NAME)

BASE_URL = "https://www.ansal.com.ar"


def sleep_random(a=2, b=5):
    time.sleep(random.uniform(a, b))


def load_login_pwd():
    supplier = Supplier.objects.get(name__iexact=SUPPLIER_NAME)

    if not supplier.login or not supplier.password:
        raise ValueError(f"Missing login/password for supplier: {SUPPLIER_NAME}")

    return {
        "LOGIN": supplier.login,
        "PASSWORD": supplier.password,
    }


def enter_ansal(page, login_data):
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=60000)
    sleep_random(3, 6)

    page.get_by_role("link", name="Clientes").click()
    sleep_random(3, 6)

    page.wait_for_selector('input[placeholder="Cliente"]', timeout=30000)

    page.fill('input[placeholder="Cliente"]', login_data["LOGIN"])
    sleep_random(1, 2)

    page.fill('input[placeholder="Contraseña"]', login_data["PASSWORD"])
    sleep_random(1, 2)

    page.get_by_role("button").click()
    sleep_random(5, 8)

    page.goto(f"{BASE_URL}/search", wait_until="domcontentloaded", timeout=60000)
    sleep_random(4, 7)

    logger.info("Login Ansal: ✅")


def parse_price(price_text):
    logger.info(f"price_orig: {price_text}")

    if not price_text:
        return None

    value = str(price_text).strip()

    value = (
        value
        .replace("$", "")
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
    if "," in value and "." in value:
        if value.find(",") < value.find("."):
            value = value.replace(",", "")
        else:
            value = value.replace(".", "").replace(",", ".")

    elif "," in value:
        value = value.replace(",", ".")

    elif "." in value:
        parts = value.split(".")

        # 207.648 -> 207648
        if len(parts) > 1 and len(parts[-1]) == 3:
            value = value.replace(".", "")

    try:
        parsed = Decimal(value).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
        logger.info(f"price_parsed: {parsed}")
        return str(parsed)

    except (InvalidOperation, ValueError):
        logger.warning(f"Could not parse Ansal price: raw={price_text}, cleaned={value}")
        return None


def get_code_from_url(url):
    if not url:
        return ""

    return url.rstrip("/").split("/")[-1].strip()


def get_prods(html):
    soup = BeautifulSoup(html, "html.parser")

    cards = soup.find_all("div", class_="ContenedorProductos")
    logger.info(f"Ansal cards found: {len(cards)}")

    result = []

    for card in cards:
        try:
            link_tag = card.find("a", class_="result-item--grid__top")
            img_tag = card.find("img", class_="ImgGrid")
            price_tag = card.select_one("div.Precios span.price")
            form_tag = card.find("form", attrs={"role": "add-to-cart"})

            if not link_tag or not price_tag:
                logger.warning("Skip Ansal card: missing link or price")
                continue

            url = link_tag.get("href", "").strip()

            if url and not url.startswith("http"):
                url = BASE_URL + url

            code = ""

            if form_tag and form_tag.get("product"):
                code = str(form_tag.get("product")).strip()

            if not code:
                code = get_code_from_url(url)

            title = ""

            if img_tag and img_tag.get("alt"):
                title = img_tag.get("alt").strip()

            if not title:
                title = link_tag.get_text(" ", strip=True)

            price = parse_price(price_tag.get_text(strip=True))

            if not code or not title or price is None:
                logger.warning(
                    f"Skip Ansal card: code={code}, title={title}, price={price}"
                )
                continue

            result.append(
                {
                    "code": code,
                    "title": title,
                    "price": price,
                    "url": url,
                    "currency": "ARS",
                }
            )

        except Exception as e:
            logger.warning(f"Skip Ansal product card: {e}")
            continue

    logger.info(f"Ansal products parsed: {len(result)}")

    return result


def save_to_json(prods, json_file=JSON_FILE):
    os.makedirs(os.path.dirname(json_file), exist_ok=True)

    if os.path.exists(json_file):
        with open(json_file, "r", encoding="utf-8") as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                existing_data = []
    else:
        existing_data = []

    existing_data.extend(prods)

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved {len(prods)} products to JSON")


def clear_json(json_file=JSON_FILE):
    os.makedirs(os.path.dirname(json_file), exist_ok=True)

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)


def save_debug_files(page, page_num):
    try:
        page.screenshot(path=str(SCREENSHOT_PATH), full_page=True)
        logger.info(f"Screenshot saved: {SCREENSHOT_PATH}")
    except Exception as e:
        logger.warning(f"Failed to save screenshot: {e}")

    try:
        debug_html_path = SCREENSHOT_PATH.with_name(
            f"{PARSER_NAME}_page_{page_num}_debug.html"
        )

        with open(debug_html_path, "w", encoding="utf-8") as f:
            f.write(page.content())

        logger.info(f"Debug HTML saved: {debug_html_path}")

    except Exception as e:
        logger.warning(f"Failed to save debug HTML: {e}")


def collect_prods(page):
    total_products = 0
    page_num = 0

    while True:
        page_num += 1

        url = (
            f"{BASE_URL}/search"
            f"?q=&page={page_num}&viewMode=grid&orderBy=orden%20asc&moneda=ARS"
        )

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            sleep_random(4, 8)

            html = page.content()
            prods = get_prods(html)

        except (Error, TimeoutError) as e:
            logger.warning(f"Playwright error on page {page_num}: {e}")
            sleep_random(15, 25)

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                sleep_random(5, 10)

                html = page.content()
                prods = get_prods(html)

            except Exception as retry_error:
                logger.exception(f"Retry failed on page {page_num}: {retry_error}")
                save_debug_files(page, page_num)
                break

        if not prods:
            logger.info("No more products")
            save_debug_files(page, page_num)
            break

        save_to_json(prods)
        total_products += len(prods)

        logger.info(f"Page {page_num}: {len(prods)} products")
        sleep_random(5, 10)

    logger.info(f"Parsing finished. Total products: {total_products}")
    return total_products


def run(retail=False):
    logger.info("Ansal parser started")
    logger.info(f"Mode: {'Retail' if retail else 'Wholesale'}")

    clear_json()

    login_data = None

    if not retail:
        login_data = load_login_pwd()

    total_products = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            if login_data:
                enter_ansal(page, login_data)

            total_products = collect_prods(page)

            api_result = send_products_json(
                JSON_FILE,
                SUPPLIER_NAME,
                parser_name=PARSER_NAME,
                price_type="retail" if retail else "wholesale",
            )

            return {
                "status": "ok",
                "supplier": SUPPLIER_NAME,
                "parser_name": PARSER_NAME,
                "price_type": "retail" if retail else "wholesale",
                "products": total_products,
            }

        except Exception as e:
            logger.exception(f"Ansal parser failed: {e}")
            save_debug_files(page, 0)
            raise

        finally:
            browser.close()
            logger.info(
            f"Ansal parsing finished. "
            f"Total products: {total_products}. API result: {api_result}"
            )


if __name__ == "__main__":
    run()