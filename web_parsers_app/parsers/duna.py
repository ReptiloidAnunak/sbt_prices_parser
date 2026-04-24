
import os
import time
import random
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
from dotenv import load_dotenv
from logger import get_logger
from send_json import send_products_json
from settings import JSON_FILE, SUPPLIER_NAME

logger = get_logger()


def load_login_pwd():
    load_dotenv('.env')
    return {
            'LOGIN': os.environ.get('LOGIN'),
            'PASSWORD': os.environ.get('PASSWORD')
            }


login_data = load_login_pwd()

# -----------------------------
# Utils
# -----------------------------
def sleep_random(a=2, b=5):
    time.sleep(random.uniform(a, b))


# -----------------------------
# Login
# -----------------------------
def enter_duna(page):
    page.goto("https://www.agrupacionduna.com/login")
    page.wait_for_load_state("domcontentloaded")
    sleep_random(2, 4)
    logger.info('Login Duna: ✅')


def close_popup_if_exists(page):
    try:
        page.locator("#CheckBoxPopup").click(timeout=3000)
        logger.info("Popup closed")
    except:
        logger.info("No popup")


def login(page):

    page.wait_for_selector('input[name="EmailInicioSesion"]', timeout=10000)

    page.locator('input[name="EmailInicioSesion"]').fill(login_data['LOGIN'])
    page.locator('input[name="PassInicioSesion"]').fill(login_data['PASSWORD'])

    page.locator('form.FrmLogin a.Boton').click()

    page.wait_for_load_state("networkidle")
    sleep_random(3, 6)


def click_load_more(page):
    while True:
        try:
            items = page.locator(".CeldaArticulo")
            count_before = items.count()

            load_more = page.locator("p.load-more")

            if not load_more.is_visible():
                logger.info("No button")
                sleep_random(2,4)
                load_more = page.locator("p.load-more")
                if not load_more.is_visible():
                    logger.info("No button")
                    time.sleep(10)
                    break

            load_more.scroll_into_view_if_needed()
            sleep_random(2, 5)


            load_more.click()
            logger.info("VER MÁS")

            page.wait_for_function(
                """(count) => document.querySelectorAll('.CeldaArticulo').length > count""",
                arg=count_before,
                timeout=10000
            )

        except Exception as e:
            logger.info("Стоп:", e)
            break
        
# -----------------------------
# Main
# -----------------------------
def get_prods_dicts(page) -> list:
    soup = BeautifulSoup(page.content(), 'html.parser')
    prods_grid = soup.find(id='TablaArticulos')
    prods_cards = prods_grid.find_all(class_='CeldaArticulo')
    
    cards = [
        {
            "code": card.find('p', class_='CodigoArticulo Italic').text.strip(),
            "title": card.find('p', class_='NombreArticulo').text.strip(),
            "price": float(card.find("div", class_='PrecioFinal').find('p', class_='Precio').text.strip().split(',')[0].replace('.', ''))
        } for card in prods_cards
        ]
    return cards



def save_to_json(prods):
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                existing_data = []
    else:
        existing_data = []

    existing_data.extend(prods)

    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved {len(prods)} products to JSON")


def run():
    if os.path.exists(JSON_FILE):
        os.remove(JSON_FILE)
        
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            slow_mo=50
        )
        page = browser.new_page()

        try:
            enter_duna(page)

            close_popup_if_exists(page)

            login(page)

            logger.info("Login attempt finished")
            logger.info(f"Current URL: {page.url}")
            sleep_random(3, 5)

            page.goto('https://www.agrupacionduna.com/articulos.php?id_familia=9592')
            sleep_random(2, 10)
            click_load_more(page)
            cards = get_prods_dicts(page)
        finally:
            save_to_json(cards)
            browser.close()

    send_products_json(JSON_FILE, SUPPLIER_NAME)


if __name__ == "__main__":
    run()