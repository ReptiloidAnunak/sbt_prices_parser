import json
import os
import random
import time

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from playwright._impl._errors import Error

from web_parsers_app.logger import get_logger
from web_parsers_app.send_json import send_products_json
from web_parsers_app.settings import JSON_FILE


logger = get_logger()

SUPPLIER_NAME = "Electrofrig"
BASE_URL = "http://www.electrofrig.com.ar/es"
LOGIN_URL = f"{BASE_URL}/login.php"
CATALOG_URL = f"{BASE_URL}/catalogo_listado.php"


def sleep_random(a=2, b=5):
    time.sleep(random.uniform(a, b))


def load_login_pwd():
    load_dotenv(".env")

    return {
        "LOGIN": os.environ.get("ELECTROFRIG_LOGIN") or os.environ.get("LOGIN"),
        "PASSWORD": os.environ.get("ELECTROFRIG_PASSWORD") or os.environ.get("PASSWORD"),
    }


def login_electrofrig(page, login_data):
    page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60000)

    sleep_random()

    page.locator("#email").fill(login_data["LOGIN"])
    page.locator("#clave").fill(login_data["PASSWORD"])

    sleep_random()

    page.locator("a.shadowtext").click()
    page.wait_for_load_state("networkidle", timeout=60000)

    logger.info("Login Electrofrig: ✅")

    sleep_random(5)


def get_products(soup):
    products_cards = soup.find_all("div", class_="listadoLogueado item")
    result = []

    for card in products_cards:
        try:
            code = card.find("div", class_="id").text.strip()
            title = card.find("h2").text.strip()
            price_text = card.find("div", class_="precio").find_all("span")[1].text
            price = float(price_text.replace(".", "").replace(",", "."))

            result.append(
                {
                    "code": code,
                    "title": title,
                    "price": price,
                }
            )

        except Exception as e:
            logger.warning(f"Skip Electrofrig product card: {e}")
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


def run():
    logger.info("Electrofrig parser started")

    login_data = load_login_pwd()

    if not login_data["LOGIN"] or not login_data["PASSWORD"]:
        raise ValueError("Missing Electrofrig login/password in .env")

    clear_json()

    total_products = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            login_electrofrig(page, login_data)

            current_page = 1

            while True:
                link = f"{CATALOG_URL}?page={current_page}"

                try:
                    page.goto(link, wait_until="domcontentloaded", timeout=60000)
                except Error:
                    logger.warning(f"Page load error. Retry page {current_page}")
                    time.sleep(5)
                    page.goto(link, wait_until="domcontentloaded", timeout=60000)

                logger.info(f"Page {current_page}")

                soup = BeautifulSoup(page.content(), "html.parser")
                products = get_products(soup)

                if not products:
                    logger.info("No more products")
                    break

                save_to_json(products)
                total_products += len(products)

                current_page += 1
                sleep_random(3, 5)

            send_products_json(JSON_FILE, SUPPLIER_NAME)

            return {
                "status": "ok",
                "supplier": SUPPLIER_NAME,
                "products": total_products,
            }

        except Exception as e:
            logger.exception(f"Electrofrig parser failed: {e}")
            raise

        finally:
            browser.close()


if __name__ == "__main__":
    run()