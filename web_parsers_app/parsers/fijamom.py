import json
import os
import random
import time

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from web_parsers_app.logger import get_logger
from web_parsers_app.settings import JSON_FILE
from web_parsers_app.send_json import send_products_json


logger = get_logger()

SUPPLIER_NAME = "Fijamom"
BASE_URL = "https://www.fijamom.com.ar"


def sleep_random(a=2, b=5):
    time.sleep(random.uniform(a, b))


def load_login_pwd():
    load_dotenv(".env")

    return {
        "LOGIN": os.environ.get("FIJAMOM_LOGIN") or os.environ.get("LOGIN"),
        "PASSWORD": os.environ.get("FIJAMOM_PASSWORD") or os.environ.get("PASSWORD"),
    }


def enter_fijamom(page, login_data):
    page.goto(f"{BASE_URL}/auth/login", wait_until="domcontentloaded", timeout=60000)

    page.wait_for_selector('input[placeholder="Correo"]', timeout=30000)

    page.fill('input[placeholder="Correo"]', login_data["LOGIN"])
    sleep_random(1, 2)

    page.fill('input[placeholder="Password"]', login_data["PASSWORD"])
    sleep_random(1, 2)

    page.get_by_role("button").click()
    page.wait_for_load_state("networkidle", timeout=60000)

    sleep_random(3, 5)

    logger.info("Login Fijamom: ✅")


def get_prods(html):
    soup = BeautifulSoup(html, "html.parser")
    card_blocks = soup.find_all("div", class_="list__init-card")

    products = []

    for card in card_blocks:
        try:
            title_tag = card.find("h6")
            price_tag = card.find("small", class_="list__prices-price")

            if not title_tag or not price_tag:
                continue

            title = title_tag.get_text(strip=True)

            if title in ["BP", "cambio", "PEDIDO F"]:
                continue

            raw_price = (
                price_tag.get_text(strip=True)
                .replace("$", "")
                .replace(".", "")
                .replace(",", ".")
                .strip()
            )

            price = float(raw_price)

            products.append(
                {
                    "code": "",
                    "title": title,
                    "price": price,
                }
            )

        except Exception as e:
            logger.warning(f"Skip Fijamom product card: {e}")
            continue

    return products


def save_to_json(prods, json_file=JSON_FILE):
    os.makedirs(os.path.dirname(json_file), exist_ok=True)

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(prods, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved {len(prods)} products to JSON")


def clear_json(json_file=JSON_FILE):
    os.makedirs(os.path.dirname(json_file), exist_ok=True)

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)


def collect_prods(page):
    last_height = 0
    same_count = 0

    while True:
        page.evaluate("window.scrollBy(0, 400)")
        page.wait_for_timeout(800)

        new_height = page.evaluate("document.body.scrollHeight")

        if new_height == last_height:
            same_count += 1
        else:
            same_count = 0

        if same_count >= 3:
            break

        last_height = new_height

    products = get_prods(page.content())
    save_to_json(products)

    return len(products)


def run():
    logger.info("Fijamom parser started")

    login_data = load_login_pwd()

    if not login_data["LOGIN"] or not login_data["PASSWORD"]:
        raise ValueError("Missing Fijamom login/password in .env")

    clear_json()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            enter_fijamom(page, login_data)

            page.goto(
                f"{BASE_URL}/productos",
                wait_until="domcontentloaded",
                timeout=60000,
            )
            page.wait_for_load_state("networkidle", timeout=60000)

            total_products = collect_prods(page)

            send_products_json(JSON_FILE, SUPPLIER_NAME)

            return {
                "status": "ok",
                "supplier": SUPPLIER_NAME,
                "products": total_products,
            }

        except Exception as e:
            logger.exception(f"Fijamom parser failed: {e}")
            raise

        finally:
            browser.close()


if __name__ == "__main__":
    run()