import re
import time
import random
from pathlib import Path

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError, Error


categories_links = [
    "https://www.bellinihnos.com.ar/categoria-producto/compresores/",
    "https://www.bellinihnos.com.ar/categoria-producto/gas-refrigerante/",
    "https://www.bellinihnos.com.ar/categoria-producto/herramientas/",
    "https://www.bellinihnos.com.ar/categoria-producto/insumos-instalacion-aa/",
    "https://www.bellinihnos.com.ar/categoria-producto/metales/",
    "https://www.bellinihnos.com.ar/categoria-producto/refrigeracion-comercial/",
    "https://www.bellinihnos.com.ar/categoria-producto/repuestos-refrigeracion/",
    "https://www.bellinihnos.com.ar/categoria-producto/ventilacion/",
    "https://www.bellinihnos.com.ar/categoria-producto/ferreteria/",
]

DEBUG_DIR = Path("debug_bellini")
DEBUG_DIR.mkdir(exist_ok=True)


def sleep_random(a=2, b=5):
    time.sleep(random.uniform(a, b))


def parse_price(text):
    if not text:
        return None

    text = (
        str(text)
        .replace("$", "")
        .replace(".", "")
        .replace(",", ".")
        .strip()
    )
    text = re.sub(r"[^\d.]", "", text)

    try:
        return float(text)
    except ValueError:
        return None


def get_page_url(category_url, page_num):
    if page_num == 1:
        return category_url
    return category_url.rstrip("/") + f"/page/{page_num}/"


def parse_products(html, category_url):
    soup = BeautifulSoup(html, "html.parser")
    products = []

    cards = soup.select("li.product")

    for card in cards:
        title_tag = card.select_one("h2.woocommerce-loop-product__title")
        price_tag = card.select_one("span.price")
        link_tag = card.select_one("a.woocommerce-LoopProduct-link, a.woocommerce-loop-product__link")

        if not title_tag or not link_tag:
            continue

        title = title_tag.get_text(" ", strip=True)
        url = link_tag.get("href", "").strip()
        price_raw = price_tag.get_text(" ", strip=True) if price_tag else ""

        products.append({
            "title": title,
            "price": parse_price(price_raw),
            "price_raw": price_raw,
            "url": url,
            "category_url": category_url,
        })

    return products


def get_html(page, url, debug_name):
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        sleep_random(4, 7)

        html = page.content()

        debug_path = DEBUG_DIR / f"{debug_name}.html"
        debug_path.write_text(html, encoding="utf-8")

        return html

    except (PlaywrightTimeoutError, Error) as e:
        print(f"LOAD ERROR: {url}")
        print(e)

        try:
            html = page.content()
            debug_path = DEBUG_DIR / f"{debug_name}_error.html"
            debug_path.write_text(html, encoding="utf-8")
        except Exception:
            pass

        return ""


def scrape_category(page, category_url, max_pages=100):
    total = 0
    category_slug = category_url.rstrip("/").split("/")[-1]

    for page_num in range(1, max_pages + 1):
        url = get_page_url(category_url, page_num)

        print("\n" + "-" * 80)
        print(f"PAGE {page_num}: {url}")

        html = get_html(page, url, f"{category_slug}_page_{page_num}")

        if not html:
            print("No HTML — stop category")
            break

        products = parse_products(html, category_url)

        if not products:
            print("No products — stop category")
            break

        for product in products:
            print(
                f"{product['title']} | "
                f"{product['price']} | "
                f"{product['url']}"
            )

        total += len(products)
        sleep_random(4, 8)

    print(f"CATEGORY DONE: {total} products")
    return total


def main():
    total_all = 0

    with sync_playwright() as p:
        browser = p.firefox.launch(
            headless=False,
            slow_mo=150,
        )

        context = browser.new_context(
            viewport={"width": 1366, "height": 768},
            locale="es-AR",
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64; rv:148.0) "
                "Gecko/20100101 Firefox/148.0"
            ),
            extra_http_headers={
                "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
            },
        )

        page = context.new_page()

        try:
            for category_url in categories_links:
                print("\n" + "=" * 80)
                print(f"CATEGORY: {category_url}")
                print("=" * 80)

                total_all += scrape_category(page, category_url)

            print("\nDONE")
            print(f"TOTAL PRODUCTS: {total_all}")

        finally:
            browser.close()


if __name__ == "__main__":
    main()