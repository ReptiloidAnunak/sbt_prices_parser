from playwright.sync_api import sync_playwright
from playwright._impl._errors import Error
import time
import random
from bs4 import BeautifulSoup
import os
import json
from dotenv import load_dotenv

def load_login_pwd():
    load_dotenv('.env')
    return {
            'LOGIN': os.environ.get('LOGIN'),
            'PASSWORD': os.environ.get('PASSWORD')
            }


login_data = load_login_pwd()

JSON_FILE = "electrofrig_products.json"

def sleep_random(a=2, b=5):
    time.sleep(random.uniform(a, b))


def login_electrofrig(page):
    page.goto("http://www.electrofrig.com.ar/es/login.php")
    sleep_random()

    page.locator("#email").fill(login_data["LOGIN"])
    page.locator("#clave").fill(login_data["PASSWORD"])

    sleep_random()
    page.locator("a.shadowtext").click()
    page.wait_for_load_state("networkidle")
    print("Login - OK")

    sleep_random(5)


def get_products(soup: BeautifulSoup):
    products_cards = soup.find_all("div", class_="listadoLogueado item")

    cards = [
        {
            "code": card.find('div', class_='id').text.strip(),
            "title": card.find("h2").text.strip(),
            "price": float(card.find("div", class_='precio').find_all("span")[1].text.replace('.', '').replace(',', '.'))
        } for card in products_cards
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

    print(f"Saved {len(prods)} products to JSON")

def run():
    print("Electrogrig parser")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        login_electrofrig(page)

        index_link = "http://www.electrofrig.com.ar/es/catalogo_listado.php"
        page.goto(index_link)

        current_page = 164

        while True:
            link = f"{index_link}?page={current_page}"
            try:
                page.goto(link)
            except Error:
                time.sleep(5)
                page.goto(link)
            print(f"Page {current_page}")

            content = page.content()
            soup = BeautifulSoup(content, 'html.parser')
            products = get_products(soup)
            if not products:
                break
            save_to_json(products)
            current_page += 1
            sleep_random(3, 5)

        browser.close()


if __name__ == "__main__":
    run()