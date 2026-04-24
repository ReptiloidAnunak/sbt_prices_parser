import json
import os
import random
import time

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from web_parsers_app.logger import get_logger
from web_parsers_app.send_json import send_products_json
from web_parsers_app.settings import JSON_FILE


logger = get_logger()

SUPPLIER_NAME = "Duna"
BASE_URL = "https://www.agrupacionduna.com"


def sleep_random(a=2, b=5):
    time.sleep(random.uniform(a, b))


def load_login_pwd():
    load_dotenv(".env")

    return {
        "LOGIN": os.environ.get("DUNA_LOGIN") or os.environ.get("LOGIN"),
        "PASSWORD": os.environ.get("DUNA_PASSWORD") or os.environ.get("PASSWORD"),
    }


def enter_duna(page):
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=60000)
    sleep_random(2, 4)
    logger.info("Login Duna page opened")


def close_popup_if_exists(page):
    try:
        page.locator("#CheckBoxPopup").click(timeout=3000)
        logger.info("Popup closed")
    except Exception:
        logger.info("No popup")


def login(page, login_data):
    page.wait_for_selector('input[name="EmailInicioSesion"]', timeout=30000)

    page.locator('input[name="EmailInicioSesion"]').fill(login_data["LOGIN"])
    page.locator('input[name="PassInicioSesion"]').fill(login_data["PASSWORD"])

    page.locator("form.FrmLogin a.Boton").click()

    page.wait_for_load_state("networkidle", timeout=60000)
    sleep_random(3, 6)

    logger.info("Login Duna: ✅")


def click_load_more(page):
    while True:
        try:
            items = page.locator(".CeldaArticulo")
            count_before = items.count()

            load_more = page.locator("p.load-more")

            if not load_more.is_visible():
                logger.info("No load-more button")
                sleep_random(2, 4)

                load_more = page.locator("p.load-more")

                if not load_more.is_visible():
                    logger.info("No load-more button after retry")
                    break

            load_more.scroll_into_view_if_needed()
            sleep_random(2, 5)

            load_more.click()
            logger.info("Clicked VER MÁS")

            page.wait_for_function(
                """(count) => document.querySelectorAll('.CeldaArticulo').length > count""",
                arg=count_before,
                timeout=15000,
            )

        except Exception as e:
            logger.info(f"Stop loading more products: {e}")
            break


def get_prods_dicts(page):
    soup = BeautifulSoup(page.content(), "html.parser")
    prods_grid = soup.find(id="TablaArticulos")

    if not prods_grid:
        logger.warning("Products grid not found")
        return []

    prods_cards = prods_grid.find_all(class_="CeldaArticulo")
    result = []

    for card in prods_cards:
        try:
            code = card.find("p", class_="CodigoArticulo Italic").text.strip()
            title = card.find("p", class_="NombreArticulo").text.strip()

            price_text = (
                card.find("div", class_="PrecioFinal")
                .find("p", class_="Precio")
                .text
                .strip()
            )

            price = float(price_text.split(",")[0].replace(".", ""))

            result.append(
                {
                    "code": code,
                    "title": title,
                    "price": price,
                }
            )

        except Exception as e:
            logger.warning(f"Skip Duna product card: {e}")
            continue

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
    logger.info("Duna parser started")

    login_data = load_login_pwd()

    if not login_data["LOGIN"] or not login_data["PASSWORD"]:
        raise ValueError("Missing Duna login or password in .env")

    clear_json()

    cards = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=50)
        page = browser.new_page()

        try:
            enter_duna(page)
            close_popup_if_exists(page)
            login(page, login_data)

            logger.info(f"Current URL: {page.url}")

            page.goto(
                f"{BASE_URL}/articulos.php?id_familia=9592",
                wait_until="domcontentloaded",
                timeout=60000,
            )

            sleep_random(2, 10)

            click_load_more(page)

            cards = get_prods_dicts(page)
            save_to_json(cards)

            send_products_json(JSON_FILE, SUPPLIER_NAME)

            return {
                "status": "ok",
                "supplier": SUPPLIER_NAME,
                "products": len(cards),
            }

        except Exception as e:
            logger.exception(f"Duna parser failed: {e}")
            raise

        finally:
            browser.close()


if __name__ == "__main__":
    run()