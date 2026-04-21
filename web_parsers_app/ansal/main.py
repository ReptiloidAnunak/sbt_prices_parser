from playwright.sync_api import sync_playwright
from playwright._impl._errors import TimeoutError, Error
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import os
from dotenv import load_dotenv
import json
from logger import get_logger
from settings import JSON_FILE
from send_json import send_products_json


logger = get_logger()

# -----------------------------
# Utils
# -----------------------------

def sleep_random(a=2, b=5):
    time.sleep(random.uniform(a, b))

# -----------------------------
# Login
# -----------------------------

def load_login_pwd():
    load_dotenv('.env')
    return {
            'LOGIN': os.environ.get('LOGIN'),
            'PASSWORD': os.environ.get('PASSWORD')
            }

login_data = load_login_pwd()



def enter_ansal(page):
    page.goto("https://www.ansal.com.ar/")
    sleep_random(3, 6)

    page.get_by_role("link", name="Clientes").click()
    sleep_random(3, 6)

    page.wait_for_selector('input[placeholder="Cliente"]')

    page.fill('input[placeholder="Cliente"]', login_data['LOGIN'])
    sleep_random(1, 2)

    page.fill('input[placeholder="Contraseña"]', login_data['PASSWORD'])
    sleep_random(1, 2)

    page.get_by_role("button").click()
    sleep_random(5, 8)

    page.goto("https://www.ansal.com.ar/search")
    sleep_random(4, 7)
    logger.info('Login Ansal: ✅')

# -----------------------------
# Parse products
# -----------------------------

def get_prods(html):
    logger.info('get_prods start')
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
            price = float(price.replace(',', ''))
            sku = card.find("h4").find("span").text.strip()

            result.append({
                "code": sku,
                "title": card.find("div", class_="desc").text.strip(),
                "price": price,
                "url": "https://www.ansal.com.ar" + '/producto/' + sku
            })
        except Exception:
            continue

    return result

# -----------------------------
# Save JSON
# -----------------------------

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

# -----------------------------
# Collect
# -----------------------------

def collect_prods(page):
    try:
        page_num = 0

        while True:
            page_num += 1
            url = f"https://www.ansal.com.ar/search?q=&page={page_num}&viewMode=grid&orderBy=orden%20asc&moneda=ARS"
            try:
                page.goto(url)
                sleep_random(4, 8)

                html = page.content()
                prods = get_prods(html)

                if not prods:
                    break

                logger.info(f"Page {page_num}: {len(prods)} products")
            except (Error, TimeoutError) as e:
                logger.info(f'\n\n{e}\n\n')
                time.sleep(20)
                page.goto(url)
                sleep_random(5, 10)

                html = page.content()
                prods = get_prods(html)

                if not prods:
                    logger.info('No more products')
                    break

                logger.info(f"Page {page_num}: {len(prods)} products")
            finally:
                save_to_json(prods)
                sleep_random(5, 10)
        logger.info('Parsing is finished')
    except Exception as e:
        logger.error(e)
    finally:
        send_products_json(JSON_FILE, 'Ansal')

            

# -----------------------------
# Main
# -----------------------------

def run():
    logger.info("Ansal parser")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        logger.info("START")

        try:
            enter_ansal(page)
            collect_prods(page)
        finally:
            browser.close()
        

if __name__ == "__main__":
    run()