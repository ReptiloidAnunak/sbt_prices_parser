import time

from bs4 import BeautifulSoup
import requests


PARSER_NAME = "refrigeracion_norte"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Connection": "keep-alive",
}


def get_products():
    result = []

    page_html = requests.get(
        "https://refrigeracionnorte.com.ar/page/1/",
        headers=HEADERS,
        timeout=30,
    )
    page_html.raise_for_status()

    soup = BeautifulSoup(page_html.content, "html.parser")

    page_numbers = soup.find_all("a", class_="page-numbers")
    last_page = int(page_numbers[-2].text.strip()) if page_numbers else 1

    pages_links = [
        f"https://refrigeracionnorte.com.ar/page/{n}/"
        for n in range(1, last_page + 1)
    ]

    for link in pages_links:
        print(f"Parse: {link}")

        page_html = requests.get(link, headers=HEADERS, timeout=30)
        page_html.raise_for_status()

        soup = BeautifulSoup(page_html.content, "html.parser")

        prods_grid = soup.find("div", class_="products-container")
        if not prods_grid:
            print(f"No products grid: {link}")
            continue

        prods_cards = prods_grid.find_all("div", class_="product")

        for card in prods_cards:
            add_btn = card.find("a", class_="add_to_cart_button")
            sku = add_btn.get("data-product_sku") if add_btn else None

            title_tag = card.find("a", {"aria-label": "Post Title"})
            if not title_tag:
                continue

            title = title_tag.text.strip()
            url = title_tag["href"]

            price_tag = card.find("bdi")
            price = price_tag.text.strip() if price_tag else None

            print(sku)
            print(title)
            print(price)
            print(url)
            print("*" * 30)

            result.append({
                "code": sku,
                "title": title,
                "price": price,
                "url": url,
            })

        time.sleep(1)

    return result


def run():
    products = get_products()
    print(f"Total products: {len(products)}")
    return products


if __name__ == "__main__":
    run()