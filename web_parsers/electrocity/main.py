from playwright.sync_api import sync_playwright
import time
import random
import os
import json
from bs4 import BeautifulSoup

JSON_FILE = "electrocity_products.json"


# =========================
# UTILS
# =========================
def sleep_random(a=2, b=5):
    time.sleep(random.uniform(a, b))


# =========================
# LOGIN
# =========================
def login_electrocity(page):
    page.goto("https://electrocity.com.ar/account/login/")
    sleep_random(1, 2)

    page.fill('input[name="email"]', "sbt.international.srl@gmail.com")
    page.fill('input[name="password"]', "sbtint2026")

    sleep_random(1, 2)
    page.get_by_role("button", name="Iniciar sesión").click()
    sleep_random(3, 5)


# =========================
# POPUP
# =========================
def close_popup_if_exists(page):
    try:
        btn = page.locator('#p-close')
        if btn.count() > 0 and btn.is_visible():
            time.sleep(random.uniform(0.3, 0.8))
            btn.click(force=True)
            time.sleep(random.uniform(0.2, 0.5))
    except:
        pass


# =========================
# SAVE JSON
# =========================
def append_to_json(products):
    if not products:
        return

    with open(JSON_FILE, "a", encoding="utf-8") as f:
        for p in products:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    print(f"💾 Сохранено: +{len(products)}")


# =========================
# PARSE HTML (BS)
# =========================
def get_prod_price(prod_info_block) -> float:
    price_str = prod_info_block.find('div', class_='product-item-price-container').find('span').text.strip()
    price = float(price_str.replace('.', '').replace(',', '.').strip('$'))
    return price


def get_sku(card):
    json_prod = json.loads(card['data-variants'])[0]['sku']
    return json_prod


def parse_products_from_html(html, seen_urls):
    soup = BeautifulSoup(html, "html.parser")
    result = []
    prods_cards = soup.find_all('div', class_='product-item')
    for card in prods_cards:
        try:
            prod_info_block = card.find('div', class_="product-item-information").find("a")
            sku = get_sku(card)
            title = prod_info_block.find('div', class_='js-item-name').text.strip()
            url = prod_info_block['href']
            if not url.startswith("http"):
                url = "https://electrocity.com.ar" + url

            if url in seen_urls:
                continue
            price = get_prod_price(card)
            seen_urls.add(url)
            result.append({
                "code": sku,
                "title": title,
                "price": price,
                "url": url
            })
        except Exception as e:
            continue
    return result


# =========================
# MAIN LOADER
# =========================
def load_and_collect(page, max_rounds=50):
    seen_urls = set()

    for _ in range(max_rounds):
        close_popup_if_exists(page)

        html = page.content()
        new_products = parse_products_from_html(html, seen_urls)
        append_to_json(new_products)

        print(f"➕ Новых: {len(new_products)} | Всего: {len(seen_urls)}")

        clicked = False

        for _ in range(10):
            close_popup_if_exists(page)

            page.mouse.wheel(0, random.randint(500, 1200))
            time.sleep(random.uniform(0.6, 1.4))

            button = page.locator('a:has-text("Mostrar más productos")')

            if button.count() > 0 and button.is_visible():
                time.sleep(random.uniform(0.4, 1.0))

                try:
                    button.click(timeout=2000)
                except:
                    button.click(force=True)

                time.sleep(random.uniform(2.0, 3.5))

                clicked = True
                break

        if not clicked:
            page.mouse.wheel(0, 3000)
            time.sleep(random.uniform(2.0, 3.0))

            close_popup_if_exists(page)

            button = page.locator('a:has-text("Mostrar más productos")')

            if button.count() == 0 or not button.is_visible():
                print("✅ Конец страницы")

                # =========================
                # 🔥 ФИНАЛЬНЫЙ СБОР
                # =========================
                time.sleep(2)  # дать догрузиться
                html = page.content()
                final_products = parse_products_from_html(html, seen_urls)
                append_to_json(final_products)
                print(f"🏁 Финально добавлено: {len(final_products)} | Итого: {len(seen_urls)}")
                break


# =========================
# MAIN
# =========================
def run():
    print("🚀 Electrocity parser (BS version)")

    if os.path.exists(JSON_FILE):
        os.remove(JSON_FILE)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        login_electrocity(page)
        sleep_random(3, 5)
        page.goto("https://electrocity.com.ar/herramientas/")
        sleep_random(3, 5)
        load_and_collect(page)
        browser.close()


if __name__ == "__main__":
    run()