import json
import os
import random
import time

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from playwright._impl._errors import TimeoutError

from supplier.models import Supplier
from web_parsers_app.logger import get_logger
from web_parsers_app.settings import get_json_file, get_supplier_name
from web_parsers_app.send_json import send_products_json

PARSER_NAME = "norfrig"
logger = get_logger(PARSER_NAME)

JSON_FILE = get_json_file(PARSER_NAME)
SUPPLIER_NAME = get_supplier_name(PARSER_NAME)

BASE_URL = "https://norfrig.com.ar"


def sleep_random(a=1, b=3):
    time.sleep(random.uniform(a, b))


def load_login_pwd():
    supplier = Supplier.objects.get(name__iexact=SUPPLIER_NAME)

    if not supplier.login or not supplier.password:
        raise ValueError(f"Missing login/password for supplier: {SUPPLIER_NAME}")

    return {
        "LOGIN": supplier.login,
        "PASSWORD": supplier.password,
    }


def enter_nordfrig(page, login_data):
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=60000)

    page.wait_for_selector("#inputEmail", timeout=30000)

    page.fill("#inputEmail", login_data["LOGIN"])
    page.fill("#inputPassword", login_data["PASSWORD"])

    sleep_random()

    page.get_by_role("button").click()
    page.wait_for_load_state("networkidle", timeout=60000)

    sleep_random(3, 5)

    logger.info("Login Norfrig: ✅")


def get_prods(html):
    soup = BeautifulSoup(html, "html.parser")

    container = soup.find("div", class_="item-list")
    if not container:
        return []

    cards = container.find_all("li")
    products = []

    for card in cards:
        try:
            title_tag = card.find("h2")
            link_tag = title_tag.find("a") if title_tag else None
            price_block = card.find("span", class_="price-avanzado")

            if not (title_tag and link_tag and price_block):
                continue

            price_span = price_block.find("span")
            raw_price = (
                price_span.text.strip()
                .replace("$", "")
                .replace(".", "")
                .replace(",", ".")
            )

            url = link_tag["href"]
            if url and not url.startswith("http"):
                url = BASE_URL + url

            products.append(
                {
                    "code": "",
                    "url": url,
                    "title": title_tag.text.strip(),
                    "price": float(raw_price),
                }
            )

        except Exception as e:
            logger.warning(f"Skip Norfrig product card: {e}")
            continue

    return products


def save_to_json(prods, json_file=JSON_FILE):
    os.makedirs(os.path.dirname(json_file), exist_ok=True)

    if os.path.exists(json_file):
        with open(json_file, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    else:
        data = []

    existing_urls = {item.get("url") for item in data if item.get("url")}
    new_data = [p for p in prods if p.get("url") not in existing_urls]

    data.extend(new_data)

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved {len(new_data)} new products")

    return len(new_data)


def clear_json(json_file=JSON_FILE):
    os.makedirs(os.path.dirname(json_file), exist_ok=True)

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)


def collect_all_pages(page, max_pages=100):
    total_products = 0

    for current_page in range(1, max_pages + 1):
        url = f"{BASE_URL}/productos?page={current_page}"
        logger.info(f"Page {current_page}")

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_load_state("networkidle", timeout=60000)

        except TimeoutError:
            logger.warning(f"Timeout on page {current_page}. Retry...")
            time.sleep(10)

            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_load_state("networkidle", timeout=60000)

        html = page.content()
        prods = get_prods(html)

        if not prods:
            logger.info("No more products")
            break

        total_products += save_to_json(prods)

        sleep_random(1, 2)

    logger.info(f"Parsing finished. Total products: {total_products}")

    return total_products


def run():
    logger.info("Norfrig parser started")

    login_data = load_login_pwd()
    clear_json()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            enter_nordfrig(page, login_data)

            total_products = collect_all_pages(page, max_pages=100)

            send_products_json(JSON_FILE, SUPPLIER_NAME)

            return {
                "status": "ok",
                "supplier": SUPPLIER_NAME,
                "products": total_products,
            }

        except Exception as e:
            logger.exception(f"Norfrig parser failed: {e}")
            raise

        finally:
            browser.close()


if __name__ == "__main__":
    run()