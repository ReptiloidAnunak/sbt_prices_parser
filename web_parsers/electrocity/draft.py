from bs4 import BeautifulSoup
import json

def get_prod_price(prod_info_block) -> float:
    price_str = prod_info_block.find('div', class_='product-item-price-container').find('span').text.strip()
    price = float(price_str.replace('.', '').replace(',', '.').strip('$'))
    return price



def parse_products_from_html(html, seen_urls):
    soup = BeautifulSoup(html, "html.parser")
    result = []

    prods_cards = soup.find_all('div', class_='product-item')

    for card in prods_cards:
        

seen_urls = set()
with open('Herramientas Manuales y Eléctricas Packout.html', 'r') as file:
    parse_products_from_html(file.read(), seen_urls)