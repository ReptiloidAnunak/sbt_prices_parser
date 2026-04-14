import os
import time
import random
import json
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from playwright._impl._errors import TimeoutError

JSON_FILE = "norfrig_products.json"

# -----------------------------
# Utils
# -----------------------------
def sleep_random(a=1, b=3):
    time.sleep(random.uniform(a, b))

# -----------------------------
# Login
# -----------------------------
def enter_nordfrig(page):
    page.goto("https://norfrig.com.ar/login")

    page.wait_for_selector('#inputEmail')

    page.fill('#inputEmail', "sbt.international.srl@gmail.com")
    page.fill('#inputPassword', "sbtint2026")

    sleep_random()
    page.get_by_role('button').click()

    page.wait_for_load_state("networkidle")
    sleep_random(3, 5)

# -----------------------------
# Parse products
# -----------------------------
def get_prods(html):
    soup = BeautifulSoup(html, 'html.parser')

    container = soup.find("div", class_='item-list')
    if not container:
        return []

    cards = container.find_all("li")
    products = []

    for card in cards:
        
        title_tag = card.find('h2')
        link_tag = title_tag.find('a') if title_tag else None
        price_block = card.find('span', class_='price-avanzado')

        if not (title_tag and link_tag and price_block):
            continue

        price_span = price_block.find('span')
        raw_price = price_span.text.strip().replace('$', '').replace('.', '').replace(',', '.')

        products.append({
            "url": link_tag['href'],
            "title": title_tag.text.strip(),
            "price": float(raw_price)
        })

    return products

# -----------------------------
# Save JSON (без дублей)
# -----------------------------
def save_to_json(prods):
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except:
                data = []
    else:
        data = []

    existing_urls = {item["url"] for item in data}

    new_data = [p for p in prods if p["url"] not in existing_urls]

    data.extend(new_data)

    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(new_data)} new products")

# -----------------------------
# Pagination
# -----------------------------



def get_btn_next(html):
    soup = BeautifulSoup(html, 'html.parser')
    pagination_el = soup.find('div', id='pag')
    if not pagination_el: return False
    return True


def collect_all_pages(page, max_pages=100):
    current_page = 0
    while True:
        current_page += 1
        url = f"https://norfrig.com.ar/productos?page={current_page}"
        print(f"Page {current_page}")
        
        try:
            page.goto(url)
            page.wait_for_load_state("networkidle")
            html = page.content()
            prods = get_prods(html)
            
        except TimeoutError: 
            time.sleep(10)
            page.goto(url)
            page.wait_for_load_state("networkidle")
            html = page.content()
            prods = get_prods(html)

        save_to_json(prods)

        sleep_random(1, 2)

        if not prods:
            break

# -----------------------------
# Main
# -----------------------------
def run():
    print("Norfrig parser")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            enter_nordfrig(page)
            collect_all_pages(page, max_pages=100)

        finally:
            browser.close()

# -----------------------------
if __name__ == "__main__":
    run()