import csv
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


URL = "https://www.reld.com.ar/index_grilla.php"

PARAMS = {
    "agru_1": "",
    "agru_2": "",
    "agru_3": "",
    "articulo": "",
    "destaca": "",
    "modo_grilla": "S",
    "cant_x_pagina": "10000",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) "
        "Gecko/20100101 Firefox/125.0"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
}


def clean_text(value: str) -> str:
    return " ".join(value.replace("\xa0", " ").split())


def download_html() -> str:
    with requests.Session() as session:
        response = session.get(
            URL,
            params=PARAMS,
            headers=HEADERS,
            timeout=60,
        )

        # У RELD в HTML указан ISO-8859-1
        response.encoding = "ISO-8859-1"

        response.raise_for_status()
        return response.text


def parse_reld_products(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    products = []

    rows = soup.select('tr[id^="row-"]')

    for row in rows:
        code_link = row.select_one('a[href*="articulo.php?cod_articulo="]')
        price_cell = row.select_one("td.carrito-precio")

        if not code_link:
            continue

        code = clean_text(code_link.get_text())
        title_link = row.select_one("td.col3 h3 a")

        title = clean_text(title_link.get_text()) if title_link else ""
        price = clean_text(price_cell.get_text()) if price_cell else ""

        image_tag = row.select_one("img.img-art-grilla")
        image_url = urljoin(URL, image_tag["src"]) if image_tag and image_tag.get("src") else ""

        product_url = urljoin(URL, code_link.get("href", ""))

        products.append({
            "code": code,
            "title": title,
            "price": price,
            "image_url": image_url,
            "product_url": product_url,
        })

    return products


def save_csv(products: list[dict], filename: str = "reld_products.csv") -> None:
    with open(filename, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["code", "title", "price", "image_url", "product_url"],
        )
        writer.writeheader()
        writer.writerows(products)


def main():
    html = download_html()

    with open("reld_products.html", "w", encoding="ISO-8859-1") as file:
        file.write(html)

    products = parse_reld_products(html)

    print(f"Найдено товаров: {len(products)}")

    if products:
        print(products[0])

    save_csv(products)


if __name__ == "__main__":
    main()