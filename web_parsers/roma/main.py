from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
import time
import random

CSV_FILE = "roma_products.csv"

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

    page.fill('input[placeholder="E-mail"]', 'sbt.international.srl@gmail.com')
    sleep_random(1, 2)

    page.fill('input[placeholder="Contraseña"]', '12345678')
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
    base_url = "https://tienda.romarep.com.ar/index.php?pag="

    pagination_div = soup.find('p', align="center")

    if not pagination_div:
        return [f"{base_url}1"]

    links = pagination_div.find_all('a')
    pages = []

    for link in links:
        text = link.get_text(strip=True)
        if text.isdigit():
            pages.append(int(text))

    last_page = max(pages) if pages else 1
    return [f"{base_url}{i}" for i in range(1, last_page + 1)]

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
# Save CSV
# -----------------------------
def save_to_csv(prods):
    if not prods:
        print("No products to save")
        return

    df = pd.DataFrame(prods)

    # убираем дубли
    df = df.drop_duplicates(subset='code')

    df.to_csv(CSV_FILE, index=False)

    print(f"Saved {len(df)} unique products")

# -----------------------------
# Collect
# -----------------------------
def collect_prods(page):
    slow_scroll(page)
    html = page.content()
    sleep_random(2, 4)

    links = generate_pagination_links(html)
    print(f"Pages found: {len(links)}")

    result = []

    for link in links:
        print(f"Parsing: {link}")
        page.goto(link)
        sleep_random(1, 3)

        html = page.content()
        prods = get_prods(html)

        print(f"Found {len(prods)} products")
        result.extend(prods)

    print(f"Total collected: {len(result)}")

    save_to_csv(result)

# -----------------------------
# Main
# -----------------------------
def run():
    print("Roma parser")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            enter_roma(page)

            page.goto("https://tienda.romarep.com.ar/index.php")
            page.wait_for_load_state("networkidle")
            sleep_random(2, 5)

            collect_prods(page)

        finally:
            browser.close()

if __name__ == "__main__":
    run()