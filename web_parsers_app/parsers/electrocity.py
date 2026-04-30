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


logger = get_logger()

PARSER_NAME = "electrocity"
logger = get_logger(PARSER_NAME)

JSON_FILE = get_json_file(PARSER_NAME)
SUPPLIER_NAME = get_supplier_name(PARSER_NAME)

BASE_URL = "https://electrocity.com.ar"


# =========================
# UTILS
# =========================
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


# =========================
# LOGIN
# =========================
def login_electrocity(page, login_data):
    page.goto(f"{BASE_URL}/account/login/", wait_until="domcontentloaded")
    sleep_random(1, 2)

    page.fill('input[name="email"]', login_data["LOGIN"])
    page.fill('input[name="password"]', login_data["PASSWORD"])

    sleep_random(1, 2)
    page.get_by_role("button", name="Iniciar sesión").click()
    sleep_random(3, 5)

    logger.info("Login Electrocity: ✅")


# =========================
# POPUP
# =========================
def close_popup_if_exists(page):
    try:
        btn = page.locator("#p-close")

        if btn.count() > 0 and btn.is_visible():
            time.sleep(random.uniform(0.3, 0.8))
            btn.click(force=True)
            time.sleep(random.uniform(0.2, 0.5))
    except Exception:
        pass


# =========================
# JSON
# =========================
def append_to_json(products, json_file=JSON_FILE):
    if not products:
        return

    os.makedirs(os.path.dirname(json_file), exist_ok=True)

    with open(json_file, "a", encoding="utf-8") as f:
        for p in products:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    logger.info(f"💾 Saved: +{len(products)}")


def clear_json(json_file=JSON_FILE):
    os.makedirs(os.path.dirname(json_file), exist_ok=True)

    with open(json_file, "w", encoding="utf-8") as f:
        pass


# =========================
# PARSE HTML
# =========================
def get_prod_price(card):
    price_str = (
        card.find("div", class_="product-item-price-container")
        .find("span")
        .text.strip()
    )

    return float(price_str.replace(".", "").replace(",", ".").strip("$"))


def get_sku(card):
    return json.loads(card["data-variants"])[0]["sku"]


def parse_products_from_html(html, seen_urls):
    soup = BeautifulSoup(html, "html.parser")
    result = []

    prods_cards = soup.find_all("div", class_="product-item")

    for card in prods_cards:
        try:
            prod_info_block = (
                card.find("div", class_="product-item-information").find("a")
            )

            sku = get_sku(card)
            title = prod_info_block.find("div", class_="js-item-name").text.strip()
            url = prod_info_block["href"]

            if not url.startswith("http"):
                url = BASE_URL + url

            if url in seen_urls:
                continue

            price = get_prod_price(card)

            seen_urls.add(url)

            result.append(
                {
                    "code": sku,
                    "title": title,
                    "price": price,
                    "url": url,
                }
            )

        except Exception as e:
            logger.warning(f"Skip product: {e}")
            continue

    return result


# =========================
# LOAD ALL PRODUCTS
# =========================
def load_and_collect(page, max_rounds=50):
    seen_urls = set()

    for _ in range(max_rounds):
        close_popup_if_exists(page)

        html = page.content()
        new_products = parse_products_from_html(html, seen_urls)

        append_to_json(new_products)

        logger.info(f"➕ New: {len(new_products)} | Total: {len(seen_urls)}")

        clicked = False

        for _ in range(10):
            close_popup_if_exists(page)

            page.mouse.wheel(0, random.randint(500, 1200))
            time.sleep(random.uniform(0.6, 1.4))

            button = page.locator('a:has-text("Mostrar más productos")')

            if button.count() > 0 and button.is_visible():
                time.sleep(random.uniform(0.4, 1.0))

                try:
                    button.click(timeout=2000)
                except Exception:
                    button.click(force=True)

                time.sleep(random.uniform(2.0, 3.5))

                clicked = True
                break

        if not clicked:
            page.mouse.wheel(0, 3000)
            time.sleep(random.uniform(2.0, 3.0))

            close_popup_if_exists(page)

            button = page.locator('a:has-text("Mostrar más productos")')

            if button.count() == 0 or not button.is_visible():
                logger.info("✅ End of page")

                time.sleep(2)

                html = page.content()
                final_products = parse_products_from_html(html, seen_urls)

                append_to_json(final_products)

                logger.info(
                    f"🏁 Final added: {len(final_products)} | Total: {len(seen_urls)}"
                )

                break

    return len(seen_urls)


# =========================
# MAIN
# =========================
def run():
    logger.info("🚀 Electrocity parser started")

    login_data = load_login_pwd()

    clear_json()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            login_electrocity(page, login_data)

            sleep_random(3, 5)

            page.goto(f"{BASE_URL}/herramientas/", wait_until="domcontentloaded")

            sleep_random(3, 5)

            total = load_and_collect(page)

            api_result = send_products_json(JSON_FILE, SUPPLIER_NAME)

            logger.info(
                f"{PARSER_NAME} parsing finished. "
                f"API result: {api_result}"
                )

            return {
                "status": "ok",
                "supplier": SUPPLIER_NAME,
                "products": total,
            }

        except Exception as e:
            logger.exception(f"Electrocity parser failed: {e}")
            raise

        finally:
            browser.close()


if __name__ == "__main__":
    run()