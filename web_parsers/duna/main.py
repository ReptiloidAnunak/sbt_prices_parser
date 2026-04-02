
import os
import time
import random
import pandas as pd
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup



EMAIL = "sbt.international.srl@gmail.com"
PASSWORD = "asdfghjkl2024"


CSV_FILE = "duna_products.csv"

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


def close_popup_if_exists(page):
    try:
        page.locator("#CheckBoxPopup").click(timeout=3000)
        print("Popup closed")
    except:
        print("No popup")


def login(page):

    page.wait_for_selector('input[name="EmailInicioSesion"]', timeout=10000)

    page.locator('input[name="EmailInicioSesion"]').fill(EMAIL)
    page.locator('input[name="PassInicioSesion"]').fill(PASSWORD)

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
                print("No button")
                sleep_random(2,4)
                load_more = page.locator("p.load-more")
                if not load_more.is_visible():
                    print("No button")
                    time.sleep(10)
                    break

            load_more.scroll_into_view_if_needed()
            sleep_random(2, 5)


            load_more.click()
            print("VER MÁS")

            page.wait_for_function(
                """(count) => document.querySelectorAll('.CeldaArticulo').length > count""",
                arg=count_before,
                timeout=10000
            )

        except Exception as e:
            print("Стоп:", e)
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
            "price": card.find("div", class_='PrecioFinal').find('p', class_='Precio').text.strip().split(',')[0].replace('.', '')
        } for card in prods_cards
        ]
    return cards



def save_to_csv(prods):
    df = pd.DataFrame(prods)

    file_exists = os.path.exists(CSV_FILE)

    df.to_csv(
        CSV_FILE,
        mode='a',
        header=not file_exists,
        index=False
    )

    print(f"Saved {len(prods)} products to CSV")

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            slow_mo=50
        )
        page = browser.new_page()

        try:
            enter_duna(page)

            close_popup_if_exists(page)

            login(page)

            print("Login attempt finished")
            print("Current URL:", page.url)
            sleep_random(3, 5)

            page.goto('https://www.agrupacionduna.com/articulos.php?id_familia=9592')
            sleep_random(2, 10)
            click_load_more(page)
            cards = get_prods_dicts(page)
            save_to_csv(cards)

        finally:
            browser.close()


if __name__ == "__main__":
    run()