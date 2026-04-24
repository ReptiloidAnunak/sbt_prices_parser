import json
import os
import random
import time

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from playwright._impl._errors import TimeoutError, Error

from web_parsers_app.logger import get_logger
from web_parsers_app.settings import JSON_FILE
from web_parsers_app.send_json import send_products_json


logger = get_logger()


SUPPLIER_NAME = "Ansal"
BASE_URL = "https://www.ansal.com.ar"


def sleep_random(a=2, b=5):
    time.sleep(random.uniform(a, b))


def load_login_pwd():
    load_dotenv(".env")

    return {
        "LOGIN": os.environ.get("ANSAL_LOGIN") or os.environ.get("LOGIN"),
        "PASSWORD": os.environ.get("ANSAL_PASSWORD") or os.environ.get("PASSWORD"),
    }


def enter_ansal(page, login_data):
    page.goto(BASE_URL, wait_until="domcontentloaded")
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

    page.goto(f"{BASE_URL}/search", wait_until="domcontentloaded")
    sleep_random(4, 7)

    logger.info("Login Ansal: ✅")


def get_prods(html):
    logger.info("get_prods start")

    soup = BeautifulSoup(html, "html.parser")
    grid = soup.find("div", class_="container-fluid")

    if not grid:
        return []

    cards = grid.find_all("div", class_="ContenedorProductos")
    result = []

    for card in cards:
        try:
            price_text = card.find("div", class_="Precios").text.strip()
            price = price_text.split(" ")[-1]
            price = float(price.replace(",", ""))

            sku = card.find("h4").find("span").text.strip()
            title = card.find("div", class_="desc").text.strip()

            result.append(
                {
                    "code": sku,
                    "title": title,
                    "price": price,
                    "url": f"{BASE_URL}/producto/{sku}",
                }
            )

        except Exception as e:
            logger.warning(f"Skip product card: {e}")
            continue

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


def collect_prods(page):
    total_products = 0
    page_num = 0

    while True:
        page_num += 1
        prods = []

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
                break

        if not prods:
            logger.info("No more products")
            break

        save_to_json(prods)
        total_products += len(prods)

        logger.info(f"Page {page_num}: {len(prods)} products")
        sleep_random(5, 10)

    logger.info(f"Parsing finished. Total products: {total_products}")

    return total_products


def run():
    logger.info("Ansal parser started")

    login_data = load_login_pwd()

    if not login_data["LOGIN"] or not login_data["PASSWORD"]:
        raise ValueError("Missing Ansal login or password in .env")

    clear_json()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            enter_ansal(page, login_data)
            total_products = collect_prods(page)
            send_products_json(JSON_FILE, SUPPLIER_NAME)

            return {
                "status": "ok",
                "supplier": SUPPLIER_NAME,
                "products": total_products,
            }

        except Exception as e:
            logger.exception(f"Ansal parser failed: {e}")
            raise

        finally:
            browser.close()


if __name__ == "__main__":
    run()