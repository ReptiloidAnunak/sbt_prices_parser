from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import os
import json

CSV_FILE = "fijamom_products.csv"

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

    page.fill('input[placeholder="Correo"]', 'dashamalkina.sf@gmail.com')
    sleep_random(1, 2)

    page.fill('input[placeholder="Password"]', 'sbtinternational')
    sleep_random(1, 2)
    page.get_by_role("button").click()
    page.wait_for_load_state("networkidle")
    sleep_random(3, 5)

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
# Save CSV
# -----------------------------
def save_to_csv(prods):
    if not prods:
        print("No products to save")
        return

    df = pd.DataFrame(prods)
    df.to_csv(CSV_FILE, index=False)

    print(f"Saved {len(prods)} products")

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
    save_to_csv(prods)

# -----------------------------
# Main
# -----------------------------
def run():
    print("Fijamom parser")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            enter_fijamom(page)
            page.goto("https://www.fijamom.com.ar/productos")
            page.wait_for_load_state("networkidle")

            collect_prods(page)

        finally:
            browser.close()

if __name__ == "__main__":
    run()