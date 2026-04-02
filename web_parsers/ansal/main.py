from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import os

CSV_FILE = "ansal_products.csv"
XLSX_FILE = "ansal_products.xlsx"

# -----------------------------
# Utils
# -----------------------------

def sleep_random(a=2, b=5):
    time.sleep(random.uniform(a, b))

# -----------------------------
# Login
# -----------------------------

def enter_ansal(page):
    page.goto("https://www.ansal.com.ar/")
    sleep_random(3, 6)

    page.get_by_role("link", name="Clientes").click()
    sleep_random(3, 6)

    page.wait_for_selector('input[placeholder="Cliente"]')

    page.fill('input[placeholder="Cliente"]', '254902')
    sleep_random(1, 2)

    page.fill('input[placeholder="Contraseña"]', '30718398254')
    sleep_random(1, 2)

    page.get_by_role("button").click()
    sleep_random(5, 8)

    page.goto("https://www.ansal.com.ar/search")
    sleep_random(4, 7)

# -----------------------------
# Parse products
# -----------------------------

def get_prods(html):
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
            price = price.replace(".", "").replace(",", ".")

            result.append({
                "code": card.find("h4").find("span").text.strip(),
                "title": card.find("div", class_="desc").text.strip(),
                "price": float(price),
                "url": "https://www.ansal.com.ar" + card.find("h4").find("a")["href"]
            })
        except Exception:
            continue

    return result

# -----------------------------
# Save CSV (append!)
# -----------------------------

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

# -----------------------------
# Collect
# -----------------------------

def collect_prods(page):
    page_num = 0

    while True:
        page_num += 1

        url = f"https://www.ansal.com.ar/search?q=&page={page_num}&viewMode=grid&orderBy=orden%20asc&moneda=ARS"

        page.goto(url)
        sleep_random(4, 8)

        html = page.content()
        prods = get_prods(html)

        if not prods:
            break

        print(f"Page {page_num}: {len(prods)} products")

        # 👉 сохраняем СРАЗУ
        save_to_csv(prods)

        sleep_random(5, 10)

# -----------------------------
# CSV -> Excel
# -----------------------------

def convert_to_excel():
    if not os.path.exists(CSV_FILE):
        print("CSV not found")
        return

    df = pd.read_csv(CSV_FILE)

    # убираем дубли
    df.drop_duplicates(subset=["code"], inplace=True)

    df.to_excel(XLSX_FILE, index=False)

    # удаляем CSV
    os.remove(CSV_FILE)

    print(f"Converted to {XLSX_FILE} and removed CSV")

# -----------------------------
# Main
# -----------------------------

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            enter_ansal(page)
            collect_prods(page)
            convert_to_excel()
        finally:
            browser.close()

if __name__ == "__main__":
    run()


    https://www.ansal.com.ar/search?q=&page=334&viewMode=grid&orderBy=orden%20asc&moneda=ARS