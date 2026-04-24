from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import os
import json
from dotenv import load_dotenv
from logger import get_logger
from settings import JSON_FILE
from send_json import send_products_json


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
def enter_fijamom(page):
    page.goto("https://www.fijamom.com.ar/auth/login")

    page.wait_for_selector('input[placeholder="Correo"]')

    page.fill('input[placeholder="Correo"]', login_data['LOGIN'])
    sleep_random(1, 2)

    page.fill('input[placeholder="Password"]', login_data['PASSWORD'])
    sleep_random(1, 2)
    page.get_by_role("button").click()
    page.wait_for_load_state("networkidle")
    sleep_random(3, 5)
    logger.info('Login Fijamom: ✅')


# -----------------------------
# Parse products
# -----------------------------
def get_prods(html):
    soup = BeautifulSoup(html, "html.parser")

    card_blocks = soup.find_all("div", class_="list__init-card")
    products = []

    for card in card_blocks:
        title_tag = card.find('h6')

        price_tag = card.find('small', class_='list__prices-price')
        
        if title_tag and price_tag:
            title = title_tag.get_text(strip=True)
            if title in ["BP", "cambio", "PEDIDO F"]:
                continue
            raw_price = price_tag.get_text(strip=True).replace('$', '').replace('.', '').strip()
            try:
                price = float(raw_price)
            except ValueError:
                price = 0.0
                
            products.append({
                "title": title,
                "price": price
            })
    
    return products

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
# Scroll + Collect
# -----------------------------
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

    html = page.content()
    prods = get_prods(html)
    save_to_json(prods)

# -----------------------------
# Main
# -----------------------------
def run():
    logger.info("Fijamom parser")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            enter_fijamom(page)
            page.goto("https://www.fijamom.com.ar/productos")
            page.wait_for_load_state("networkidle")

            collect_prods(page)

        finally:
            browser.close()

    send_products_json(JSON_FILE, "Fijamom")

if __name__ == "__main__":
    run()