from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from settings import JSON_FILE
import time
import random
import json
import os
from dotenv import load_dotenv
from send_json import send_products_json
from logger import get_logger

def load_login_pwd():
    load_dotenv('.env')
    return {
            'LOGIN': os.environ.get('LOGIN'),
            'PASSWORD': os.environ.get('PASSWORD')
            }


login_data = load_login_pwd()

logger = get_logger()

# -----------------------------
# Utils
# -----------------------------
def sleep_random(a=2, b=5):
    time.sleep(random.uniform(a, b))

# -----------------------------
# Login
# -----------------------------
def enter_roma(page):
    page.goto("https://tienda.romarep.com.ar/login.php")

    page.wait_for_selector('input[placeholder="E-mail"]')

    page.fill('input[placeholder="E-mail"]', login_data['LOGIN'])
    sleep_random(1, 2)

    page.fill('input[placeholder="Contraseña"]', login_data['PASSWORD'])
    sleep_random(1, 2)

    page.get_by_role("button").click()
    page.wait_for_load_state("networkidle")
    sleep_random(3, 5)

# -----------------------------
# Scroll
# -----------------------------
def slow_scroll(page, scroll_step=300, delay=0.5):
    current_scroll_position = 0
    while True:
        total_height = page.evaluate("document.body.scrollHeight")
        current_scroll_position += scroll_step
        page.mouse.wheel(0, scroll_step)
        time.sleep(delay)

        if current_scroll_position >= total_height:
            break

# -----------------------------
# Pagination
# -----------------------------
def generate_pagination_links(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    result = []
    pagination_div = soup.find('p', align="center")
    last_page = int(pagination_div.text.split('...')[-1])

    for i in range(1, (last_page+1)):
        result.append(f"https://tienda.romarep.com.ar/index.php?pag={i}")
    return result

# -----------------------------
# Parse products
# -----------------------------
def get_prods(html):
    soup = BeautifulSoup(html, 'html.parser')
    items = soup.find_all('div', class_='prodlist')
    products = []

    for item in items:
        code = item.find('div', class_='codlist').text.strip().lstrip('Código: ')
        name_tag = item.find('h3')
        name = name_tag.get_text(strip=True) if name_tag else "N/A"

        price_el = item.find(class_='pricecarrolist').text.strip().split('\n')[0].lstrip('$ ')
        if not price_el:
            price_el = item.find(class_='pricecarrolist').text.strip().split(' + ')[0].lstrip('$ ')

        try:
            price = float(price_el.replace('.', '').replace(',', '.'))
        except ValueError:
            price = float(price_el.split(' + ')[0].replace('.', '').replace(',', '.'))

        products.append({
            'code': code,
            'name': name,
            'price': price
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
# Collect
# -----------------------------
def collect_prods(page):
    slow_scroll(page)
    html = page.content()
    sleep_random(2, 4)

    links = generate_pagination_links(html)
    logger.info(f"Pages found: {len(links)}")

    for link in links:
        logger.info(f"Parsing: {link}")
        page.goto(link)
        sleep_random(1, 3)

        html = page.content()
        prods = get_prods(html)
        logger.info(f"Found {len(prods)} products")
        save_to_json(prods)

# -----------------------------
# Main
# -----------------------------
def run():
    logger.info("Roma parser")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            enter_roma(page)

            page.goto("https://tienda.romarep.com.ar/index.php")
            page.wait_for_load_state("networkidle")
            sleep_random(2, 5)

            collect_prods(page)

        finally:
            browser.close()
            send_products_json(JSON_FILE, 'Roma Repuestos insumos')

if __name__ == "__main__":
    run()