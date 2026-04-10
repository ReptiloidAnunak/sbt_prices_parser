from bs4 import BeautifulSoup
import json
import os
import re
from data_base.tools import add_product
import random

def get_useragents() -> list:
    with open("user_agents.txt") as f:
        user_agents = [line.strip() for line in f if line.strip()]
        return user_agents

def get_all_prods_url(soup):
    view_more_url = soup.find('a', id="view-more")['href']
    return view_more_url


def get_nav_pagination(soup):
    return int(soup.find(attrs={"aria-label": "Paginación"}).find_all('li')[-2].text.strip())



def get_prods_from_page(soup):
    prods_lst = []
    prods_cards = soup.find_all('li', class_='ui-search-layout__item')
    for card in prods_cards:
        

        title_el = card.find('a', class_='poly-component__title')
        title = title_el.text.strip()
        url = title_el['href']
        price = card.find('span', class_="andes-money-amount__fraction").text.strip()

        card_dict = {
            "name": title,
            "url": url,
            "price": price
        }
        prods_lst.append(card_dict)

    print('______________________')
    return prods_lst

def get_sku(link):
    match = re.search(r'MLA\d+', link)
    try:
        return match.group()
    except AttributeError:
        return random.randint(10000, 60000)


def save_prods_db(shop, prods_lst):
    for prod in prods_lst:
        sku = get_sku(prod['url'])

        product =add_product(shop.id,
                    name=prod['name'],
                    url=prod['url'],
                    sku=sku,
                    price=prod['price'].replace('.', '')
                    )



def save_to_json(shop, prods):
    if os.path.exists(shop.json):
        with open(shop.json, 'r', encoding='utf-8') as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                existing_data = []
    else:
        existing_data = []

    existing_data.extend(prods)

    with open(shop.json, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(prods)} products to JSON")