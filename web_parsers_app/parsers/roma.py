import json
import os
import random
import time

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from supplier.models import Supplier
from web_parsers_app.logger import get_logger
from web_parsers_app.settings import get_json_file, get_supplier_name
from web_parsers_app.send_json import send_products_json

PARSER_NAME = "roma"
logger = get_logger(PARSER_NAME)
JSON_FILE = get_json_file(PARSER_NAME)
SUPPLIER_NAME = get_supplier_name(PARSER_NAME)

BASE_URL = "https://tienda.romarep.com.ar"


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


def enter_roma(page, login_data):
    page.goto(f"{BASE_URL}/login.php", wait_until="domcontentloaded", timeout=60000)

    page.wait_for_selector('input[placeholder="E-mail"]', timeout=30000)

    page.fill('input[placeholder="E-mail"]', login_data["LOGIN"])
    sleep_random(1, 2)

    page.fill('input[placeholder="Contraseña"]', login_data["PASSWORD"])
    sleep_random(1, 2)

    page.get_by_role("button").click()
    page.wait_for_load_state("networkidle", timeout=60000)

    sleep_random(3, 5)

    logger.info("Login Roma: ✅")


def slow_scroll(page, scroll_step=300, delay=0.5):
    current_scroll_position = 0

    while True:
        total_height = page.evaluate("document.body.scrollHeight")
        current_scroll_position += scroll_step
        page.mouse.wheel(0, scroll_step)
        time.sleep(delay)

        if current_scroll_position >= total_height:
            break


def generate_pagination_links(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    pagination_div = soup.find("p", align="center")

    if not pagination_div:
        return [f"{BASE_URL}/index.php"]

    try:
        last_page = int(pagination_div.text.split("...")[-1])
    except Exception:
        last_page = 1

    return [f"{BASE_URL}/index.php?pag={i}" for i in range(1, last_page + 1)]


def parse_price(price_text):
    price_text = (
        price_text.strip().split("\n")[0].replace("$", "").strip()
    )

    if " + " in price_text:
        price_text = price_text.split(" + ")[0]

    return float(price_text.replace(".", "").replace(",", "."))


def get_prods(html):
    soup = BeautifulSoup(html, "html.parser")
    items = soup.find_all("div", class_="prodlist")
    products = []

    for item in items:
        try:
            code_tag = item.find("div", class_="codlist")
            name_tag = item.find("h3")
            price_tag = item.find(class_="pricecarrolist")

            if not code_tag or not name_tag or not price_tag:
                continue

            code = code_tag.text.strip().replace("Código:", "").strip()
            title = name_tag.get_text(strip=True)
            price = parse_price(price_tag.text)

            products.append(
                {
                    "code": code,
                    "title": title,
                    "price": price,
                }
            )

        except Exception as e:
            logger.warning(f"Skip Roma product card: {e}")
            continue

    return products


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


def collect_prods(page):
    total_products = 0

    slow_scroll(page)
    html = page.content()
    sleep_random(2, 4)

    links = generate_pagination_links(html)

    logger.info(f"Pages found: {len(links)}")

    for link in links:
        logger.info(f"Parsing: {link}")

        page.goto(link, wait_until="domcontentloaded", timeout=60000)
        sleep_random(1, 3)

        html = page.content()
        prods = get_prods(html)

        logger.info(f"Found {len(prods)} products")

        if prods:
            save_to_json(prods)
            total_products += len(prods)

    return total_products


def run():
    logger.info("Roma parser started")

    login_data = load_login_pwd()
    clear_json()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            enter_roma(page, login_data)

            page.goto(
                f"{BASE_URL}/index.php",
                wait_until="domcontentloaded",
                timeout=60000,
            )
            page.wait_for_load_state("networkidle", timeout=60000)

            sleep_random(2, 5)

            total_products = collect_prods(page)

            api_result = send_products_json(JSON_FILE, SUPPLIER_NAME)

            logger.info(
                f"{PARSER_NAME} parsing finished. "
                f"API result: {api_result}"
                )

            return {
                "status": "ok",
                "supplier": SUPPLIER_NAME,
                "products": total_products,
            }

        except Exception as e:
            logger.exception(f"Roma parser failed: {e}")
            raise

        finally:
            browser.close()


if __name__ == "__main__":
    run()